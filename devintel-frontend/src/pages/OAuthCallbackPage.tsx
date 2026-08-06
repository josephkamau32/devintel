import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/axios';
import type { User } from '../lib/types';
import { Code2 } from 'lucide-react';

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
    <div className="flex min-h-screen items-center justify-center bg-surface-0">
      <div className="flex flex-col items-center gap-4 animate-fade-in">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600">
          <Code2 className="h-5 w-5 text-white" />
        </div>
        <div className="flex items-center gap-2 text-sm text-text-tertiary">
          <div className="h-4 w-4 animate-spin-slow rounded-full border-2 border-brand-500 border-t-transparent" />
          Completing sign-in…
        </div>
      </div>
    </div>
  );
}
