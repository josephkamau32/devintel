import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/axios';
import type { User } from '../lib/types';

export function OAuthCallbackPage() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const hasRun = useRef(false);

  useEffect(() => {
    // Prevent double-execution in React StrictMode
    if (hasRun.current) return;
    hasRun.current = true;

    const hash = window.location.hash;
    const params = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : hash);
    const token = params.get('access_token');

    // Clear the token from the URL immediately for security
    if (window.history.replaceState) {
      window.history.replaceState(null, '', window.location.pathname);
    }

    if (!token) {
      navigate('/login?error=oauth_failed', { replace: true });
      return;
    }

    api
      .get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(({ data }) => {
        setAuth(token, data);
        navigate('/dashboard', { replace: true });
      })
      .catch(() => {
        navigate('/login?error=oauth_failed', { replace: true });
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
