/**
 * Centralized API Client using fetch
 *
 * Features:
 * - JWT Authorization header
 * - Automatic token refresh on 401
 * - Typed GET/POST/PUT/DELETE methods
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
    private isRefreshing = false;
    private failedQueue: Array<{
        resolve: (value?: unknown) => void;
        reject: (reason?: unknown) => void;
    }> = [];

    private getHeaders(extra: Record<string, string> = {}): Record<string, string> {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...extra,
        };

        const token = localStorage.getItem('access_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    private async handleResponse<T>(response: Response, retryFn: () => Promise<T>): Promise<T> {
        if (response.ok) {
            return response.json() as Promise<T>;
        }

        // Attempt token refresh on 401
        if (response.status === 401) {
            return this.handleTokenRefresh<T>(retryFn);
        }

        // Parse error body
        let errorMessage = `Request failed with status ${response.status}`;
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
            // Response body not JSON
        }

        throw new Error(errorMessage);
    }

    private async handleTokenRefresh<T>(retryFn: () => Promise<T>): Promise<T> {
        if (this.isRefreshing) {
            // Queue this request while refresh is in progress
            return new Promise<T>((resolve, reject) => {
                this.failedQueue.push({
                    resolve: () => resolve(retryFn()),
                    reject,
                });
            });
        }

        this.isRefreshing = true;

        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }

            const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);

            // Retry all queued requests
            this.failedQueue.forEach((promise) => promise.resolve());
            this.failedQueue = [];

            // Retry original request
            return retryFn();
        } catch (error) {
            this.failedQueue.forEach((promise) => promise.reject(error));
            this.failedQueue = [];

            // Refresh failed — clear auth and redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login';

            throw error;
        } finally {
            this.isRefreshing = false;
        }
    }

    async get<T>(url: string): Promise<T> {
        const doRequest = async (): Promise<T> => {
            const response = await fetch(`${API_BASE_URL}${url}`, {
                method: 'GET',
                headers: this.getHeaders(),
            });
            if (response.ok) return response.json() as Promise<T>;
            // Skip token refresh for auth endpoints — they are intentionally unauthenticated
            if (response.status === 401 && !url.includes('/auth/')) return this.handleTokenRefresh<T>(doRequest);
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `GET ${url} failed (${response.status})`);
        };
        return doRequest();
    }

    async post<T>(url: string, data?: unknown): Promise<T> {
        const doRequest = async (): Promise<T> => {
            const response = await fetch(`${API_BASE_URL}${url}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: data ? JSON.stringify(data) : undefined,
            });
            if (response.ok) return response.json() as Promise<T>;
            if (response.status === 401) return this.handleTokenRefresh<T>(doRequest);
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `POST ${url} failed (${response.status})`);
        };
        return doRequest();
    }

    async put<T>(url: string, data?: unknown): Promise<T> {
        const doRequest = async (): Promise<T> => {
            const response = await fetch(`${API_BASE_URL}${url}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: data ? JSON.stringify(data) : undefined,
            });
            if (response.ok) return response.json() as Promise<T>;
            if (response.status === 401) return this.handleTokenRefresh<T>(doRequest);
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `PUT ${url} failed (${response.status})`);
        };
        return doRequest();
    }

    async delete<T>(url: string): Promise<T> {
        const doRequest = async (): Promise<T> => {
            const response = await fetch(`${API_BASE_URL}${url}`, {
                method: 'DELETE',
                headers: this.getHeaders(),
            });
            if (response.ok) return response.json() as Promise<T>;
            if (response.status === 401) return this.handleTokenRefresh<T>(doRequest);
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `DELETE ${url} failed (${response.status})`);
        };
        return doRequest();
    }
}

// Export singleton instance
export const apiClient = new APIClient();
export { API_BASE_URL };
export default apiClient;
