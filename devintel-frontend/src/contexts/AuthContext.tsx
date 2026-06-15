import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import apiClient from '@/lib/api-client';

export interface User {
  id: string;
  email: string;
  name: string | null;
  username: string | null;
  avatar_url: string | null;
  github_id: string | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setTokens: (access: string, refresh: string, userData: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');

        if (token && userStr) {
          setUser(JSON.parse(userStr));
          // Optionally verify token validity here by fetching /me
          // but relying on interceptors for refresh is usually enough
        }
      } catch (error) {
        console.error('Failed to restore auth state:', error);
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const setTokens = useCallback((access: string, refresh: string, userData: User) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    
    // Dispatch event for backward compatibility with components that 
    // haven't been migrated to useAuth yet
    window.dispatchEvent(new CustomEvent('user-updated', { detail: userData }));
  }, []);

  const logout = useCallback(async () => {
    try {
      // Call backend logout endpoint if we have a token
      const token = localStorage.getItem('access_token');
      if (token) {
        await apiClient.post('/api/v1/auth/logout').catch(() => {
            // Ignore errors if token is already invalid
        });
      }
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      localStorage.removeItem('csrf_token');
      setUser(null);
      window.dispatchEvent(new CustomEvent('user-updated', { detail: null }));
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await apiClient.get<User>('/api/v1/auth/me');
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      window.dispatchEvent(new CustomEvent('user-updated', { detail: userData }));
    } catch (error) {
      console.error('Failed to refresh user profile:', error);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, setTokens, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
