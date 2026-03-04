/**
 * Centralized API Client with Axios
 * 
 * Features:
 * - Request/response interceptors
 * - Automatic JWT refresh
 * - Error handling
 * - Token management
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
    private client: AxiosInstance;
    private isRefreshing = false;
    private failedQueue: Array<{
        resolve: (value?: unknown) => void;
        reject: (reason?: unknown) => void;
    }> = [];

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000, // 30 second timeout
            headers: {
                'Content-Type': 'application/json',
            },
            withCredentials: true, // Enable sending cookies for CSRF
        });

        this.setupInterceptors();
    }

    private setupInterceptors() {
        // Request interceptor - add auth token and CSRF token
        this.client.interceptors.request.use(
            (config: InternalAxiosRequestConfig) => {
                const token = localStorage.getItem('access_token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }

                // Add CSRF token for state-changing operations
                const csrfToken = localStorage.getItem('csrf_token');
                if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
                    config.headers['X-CSRF-Token'] = csrfToken;
                }

                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor - handle errors and token refresh
        this.client.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                const originalRequest = error.config as InternalAxiosRequestConfig & {
                    _retry?: boolean;
                };

                // If 401 and not already retrying, attempt token refresh
                // Skip auth endpoints — they are intentionally unauthenticated
                if (originalRequest.url?.includes('/auth/')) {
                    return Promise.reject(error);
                }

                if (error.response?.status === 401 && !originalRequest._retry) {
                    if (this.isRefreshing) {
                        // Queue this request while refresh is in progress
                        return new Promise((resolve, reject) => {
                            this.failedQueue.push({ resolve, reject });
                        })
                            .then(() => this.client(originalRequest))
                            .catch((err) => Promise.reject(err));
                    }

                    originalRequest._retry = true;
                    this.isRefreshing = true;

                    try {
                        const refreshToken = localStorage.getItem('refresh_token');
                        if (!refreshToken) {
                            throw new Error('No refresh token available');
                        }

                        // Call refresh endpoint
                        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                            refresh_token: refreshToken,
                        });

                        const { access_token } = response.data;
                        localStorage.setItem('access_token', access_token);

                        // Retry all queued requests
                        this.failedQueue.forEach((promise) => promise.resolve());
                        this.failedQueue = [];

                        // Retry original request
                        return this.client(originalRequest);
                    } catch (refreshError) {
                        // Refresh failed - clear tokens and redirect to login
                        this.failedQueue.forEach((promise) => promise.reject(refreshError));
                        this.failedQueue = [];

                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        window.location.href = '/login';

                        return Promise.reject(refreshError);
                    } finally {
                        this.isRefreshing = false;
                    }
                }

                return Promise.reject(error);
            }
        );
    }

    // HTTP Methods
    async get<T>(url: string, config = {}) {
        const response = await this.client.get<T>(url, config);
        return response.data;
    }

    async post<T>(url: string, data?: unknown, config = {}) {
        const response = await this.client.post<T>(url, data, config);
        return response.data;
    }

    async put<T>(url: string, data?: unknown, config = {}) {
        const response = await this.client.put<T>(url, data, config);
        return response.data;
    }

    async delete<T>(url: string, config = {}) {
        const response = await this.client.delete<T>(url, config);
        return response.data;
    }

    async patch<T>(url: string, data?: unknown, config = {}) {
        const response = await this.client.patch<T>(url, data, config);
        return response.data;
    }

    // Streaming endpoint for chat
    streamChat(url: string, data: unknown) {
        const token = localStorage.getItem('access_token');
        return fetch(`${API_BASE_URL}${url}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(data),
        });
    }

    // Agent Action endpoints
    async draftAgentAction(repositoryId: string, instruction: string) {
        return this.post<{ draft: { pr_title: string; pr_body: string; branch_name: string; commit_message: string; file_changes: { path: string; content: string }[] } }>(
            '/api/v1/chat/draft',
            { repository_id: repositoryId, instruction }
        );
    }

    async executeAgentAction(repositoryId: string, draftPayload: { pr_title: string; pr_body: string; branch_name: string; commit_message: string; file_changes: { path: string; content: string }[] }) {
        return this.post<{ pr_url: string; pr_number: number; branch_name: string }>(
            '/api/v1/chat/execute',
            { repository_id: repositoryId, draft: draftPayload }
        );
    }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
