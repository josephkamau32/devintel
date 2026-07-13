import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/axios';
import { useAuthStore } from '../store/authStore';
import type { TokenResponse, SignupPayload, LoginPayload, ApiError, RefreshResponse, User } from '../lib/types';
import { AxiosError } from 'axios';

function extractErrorMessage(error: unknown): string {
  const axiosErr = error as AxiosError<ApiError>;
  const detail = axiosErr?.response?.data?.detail;
  const errors = axiosErr?.response?.data?.errors;
  if (errors && errors.length > 0) {
    return errors.map((e) => e.message).join('. ');
  }
  return detail ?? 'Something went wrong. Please try again.';
}

export function useSignup() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (payload: SignupPayload) => {
      const { data } = await api.post<TokenResponse>('/auth/signup', payload);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      toast.success('Account created! Welcome to DevIntel.');
      navigate('/dashboard');
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useLogin() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (payload: LoginPayload) => {
      const { data } = await api.post<TokenResponse>('/auth/login', payload);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      toast.success(`Welcome back, ${data.user.full_name ?? data.user.email}!`);
      navigate('/dashboard');
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useLogout() {
  const { clearAuth } = useAuthStore();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async () => {
      await api.post('/auth/logout');
    },
    onSettled: () => {
      clearAuth();
      queryClient.clear();
      navigate('/login');
      toast.success('Logged out.');
    },
  });
}

export function useDemoLogin() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<TokenResponse>('/auth/demo');
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      toast.success('Welcome to the demo! Explore DevIntel AI.');
      navigate('/dashboard');
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useRestoreSession() {
  const { setAuth, clearAuth } = useAuthStore();

  return useMutation({
    mutationFn: async () => {
      const { data: refreshData } = await api.post<RefreshResponse>('/auth/refresh');
      const { data: user } = await api.get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${refreshData.access_token}` },
      });
      return { token: refreshData.access_token, user };
    },
    onSuccess: ({ token, user }) => {
      setAuth(token, user);
    },
    onError: () => {
      clearAuth();
    },
    retry: false,
  });
}
