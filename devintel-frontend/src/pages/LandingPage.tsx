import { Link } from 'react-router-dom';

export function LandingPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="max-w-3xl text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-600">
          <svg className="h-9 w-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold text-white">AI coding assistant for your GitHub codebase</h1>
        <p className="mt-4 text-lg text-slate-400">
          Search, chat, and generate pull requests with a secure AI assistant that understands your repositories.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            to="/login"
            className="rounded-lg bg-violet-600 px-5 py-3 font-medium text-white hover:bg-violet-500"
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            className="rounded-lg border border-slate-700 px-5 py-3 font-medium text-slate-200 hover:bg-slate-800"
          >
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
}
