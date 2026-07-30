import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md text-center animate-fade-in">
        {/* Glowing 404 */}
        <div className="relative mb-8">
          <span className="text-[120px] font-extrabold leading-none bg-gradient-to-b from-slate-700 to-slate-900 bg-clip-text text-transparent select-none">
            404
          </span>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-20 w-20 rounded-full bg-violet-600/20 blur-2xl" />
          </div>
        </div>

        <h1 className="mb-3 text-2xl font-bold text-white">Page not found</h1>
        <p className="mb-8 text-slate-400">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Link
            to="/"
            className="rounded-lg bg-violet-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-violet-500"
          >
            Go home
          </Link>
          <Link
            to="/dashboard"
            className="rounded-lg border border-slate-700 px-6 py-2.5 text-sm font-medium text-slate-300 transition hover:border-slate-600 hover:bg-slate-800/50"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
