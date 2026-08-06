import { Link } from 'react-router-dom';
import { Home, LayoutDashboard, FileQuestion } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4">
      <div className="w-full max-w-sm text-center animate-fade-in">
        {/* 404 display */}
        <div className="mb-6">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-3 border border-border">
            <FileQuestion className="h-7 w-7 text-text-quaternary" />
          </div>
          <p className="text-[80px] font-bold leading-none text-surface-4 select-none">
            404
          </p>
        </div>

        <h1 className="mb-2 text-h3 text-text-primary">Page not found</h1>
        <p className="mb-7 text-body text-text-tertiary">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col items-center gap-2.5 sm:flex-row sm:justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-500"
          >
            <Home className="h-4 w-4" />
            Go home
          </Link>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg border border-border-medium px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary hover:bg-surface-3"
          >
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
