import { useEffect, useRef } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useRestoreSession } from '../hooks/useAuth';
import { Code2 } from 'lucide-react';

export function AuthGuard() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  const restoreSession = useRestoreSession();
  const hasAttemptedRestore = useRef(false);

  useEffect(() => {
    if (!isAuthenticated && !hasAttemptedRestore.current) {
      hasAttemptedRestore.current = true;
      restoreSession.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  if (!isAuthenticated && restoreSession.isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-0">
        <div className="flex flex-col items-center gap-4 animate-fade-in">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600">
            <Code2 className="h-5 w-5 text-white" />
          </div>
          <div className="flex items-center gap-2 text-sm text-text-tertiary">
            <div className="h-4 w-4 animate-spin-slow rounded-full border-2 border-brand-500 border-t-transparent" />
            Restoring session…
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
