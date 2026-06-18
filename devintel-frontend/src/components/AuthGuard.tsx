import { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useRestoreSession } from '../hooks/useAuth';

export function AuthGuard() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  const restoreSession = useRestoreSession();

  useEffect(() => {
    if (!isAuthenticated && restoreSession.isIdle) {
      restoreSession.mutate();
    }
  }, [isAuthenticated, restoreSession]);

  if (!isAuthenticated && restoreSession.isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-violet-600 border-t-transparent" />
          <p className="text-sm text-slate-400">Restoring session…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
