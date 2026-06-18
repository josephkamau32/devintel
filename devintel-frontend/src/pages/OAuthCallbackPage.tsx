import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/axios';
import type { User } from '../lib/types';

export function OAuthCallbackPage() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.replace('#', ''));
    const token = params.get('access_token');

    if (!token) {
      navigate('/login?error=oauth_failed');
      return;
    }

    api
      .get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(({ data }) => {
        setAuth(token, data);
        navigate('/dashboard');
      })
      .catch(() => {
        navigate('/login?error=oauth_failed');
      });
  }, [navigate, setAuth]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-violet-600 border-t-transparent" />
        <p className="text-sm text-slate-400">Completing sign-in…</p>
      </div>
    </div>
  );
}
