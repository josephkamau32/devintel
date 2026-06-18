import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/axios';
import { useAuthStore } from '../store/authStore';
import type { User } from '../lib/types';

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());

  return useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const { data } = await api.get<User>('/auth/me');
      return data;
    },
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 10,
  });
}
