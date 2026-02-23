/**
 * Authentication helpers for GitHub OAuth flow.
 */

import { apiClient } from './api-client';

export interface AuthUser {
    id: string;
    email: string | null;
    name: string | null;
    avatar_url: string | null;
    github_id: string;
    created_at?: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: AuthUser;
}

/**
 * Start GitHub OAuth login flow.
 * Calls the backend to get the GitHub authorize URL, then redirects.
 */
export async function initiateGithubLogin(): Promise<void> {
    const data = await apiClient.get<{ url: string }>('/api/v1/auth/github');
    window.location.href = data.url;
}

/**
 * Log in with email and password.
 */
export async function signInWithEmail(email: string, password: string): Promise<AuthUser> {
    const data = await apiClient.post<TokenResponse>('/api/v1/auth/login', {
        username: email, // Backend expect 'username' which is used for email in this system
        password: password
    });

    // Store auth data in localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));

    // Dispatch event so other components can react
    window.dispatchEvent(new CustomEvent('user-updated', { detail: data.user }));

    return data.user;
}

/**
 * Exchange the OAuth code for tokens and store auth data.
 * Called from the AuthCallback page after GitHub redirects back.
 */
export async function handleAuthCallback(code: string): Promise<AuthUser> {
    const data = await apiClient.get<TokenResponse>(
        `/api/v1/auth/github/callback?code=${encodeURIComponent(code)}`
    );

    // Store auth data in localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));

    // Dispatch event so other components can react
    window.dispatchEvent(new CustomEvent('user-updated', { detail: data.user }));

    return data.user;
}

/**
 * Get the currently stored user, or null if not authenticated.
 */
export function getCurrentUser(): AuthUser | null {
    try {
        const userJson = localStorage.getItem('user');
        if (!userJson) return null;
        return JSON.parse(userJson) as AuthUser;
    } catch {
        return null;
    }
}

/**
 * Returns display-safe name: real name → email prefix → 'User'
 */
export function getDisplayName(): string {
    const user = getCurrentUser();
    if (!user) return 'User';
    if (user.name) return user.name;
    if (user.email) return user.email.split('@')[0];
    return 'User';
}

/**
 * Check if user is currently authenticated (has tokens stored).
 */
export function isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
}

/**
 * Log the user out by clearing all stored auth data.
 */
export function logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.dispatchEvent(new CustomEvent('user-updated', { detail: null }));
    window.location.href = '/login';
}
