import { useState, FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useLogin, useDemoLogin } from '../hooks/useAuth';
import { Code2, Github, Play, AlertCircle } from 'lucide-react';

export function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' });
  const login = useLogin();
  const demoLogin = useDemoLogin();
  const [searchParams] = useSearchParams();
  const [oauthError, setOauthError] = useState<string | null>(
    searchParams.get('error') === 'oauth_failed'
      ? 'GitHub sign-in failed. Please try again or use email login.'
      : null,
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.email || !form.password) return;
    setOauthError(null);
    login.mutate(form);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4">
      <div className="relative z-10 w-full max-w-[380px] animate-slide-up">
        {/* Logo + heading */}
        <div className="mb-7 text-center">
          <Link to="/" className="inline-block">
            <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 transition-transform hover:scale-105">
              <Code2 className="h-5 w-5 text-white" />
            </div>
          </Link>
          <h1 className="text-h3 text-text-primary">Welcome back</h1>
          <p className="mt-1 text-body-sm text-text-tertiary">
            Sign in to your DevIntel account
          </p>
        </div>

        {oauthError && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-status-error/20 bg-status-error-muted px-3.5 py-2.5 text-sm text-status-error animate-slide-down">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {oauthError}
          </div>
        )}

        {/* Demo login */}
        <button
          onClick={() => demoLogin.mutate()}
          disabled={demoLogin.isPending}
          className="mb-2.5 flex w-full items-center justify-center gap-2.5 rounded-lg border border-status-success/20 bg-status-success-muted px-4 py-2.5 text-sm font-medium text-status-success transition-all hover:bg-green-500/15 hover:border-green-500/30 disabled:opacity-50"
        >
          {demoLogin.isPending ? (
            <div className="h-4 w-4 animate-spin-slow rounded-full border-2 border-status-success border-t-transparent" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Try Demo — No account needed
        </button>

        {/* GitHub OAuth */}
        <a
          href={`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api/v1/auth/github`}
          className="mb-2.5 flex w-full items-center justify-center gap-2.5 rounded-lg border border-border-medium bg-surface-3 px-4 py-2.5 text-sm font-medium text-text-primary transition-all hover:bg-surface-4 hover:border-border-strong"
        >
          <Github className="h-4.5 w-4.5" />
          Continue with GitHub
        </a>

        {/* Divider */}
        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-surface-0 px-3 text-xs text-text-quaternary">
              or sign in with email
            </span>
          </div>
        </div>

        {/* Email form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <Input
            label="Email"
            type="email"
            placeholder="jane@company.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <Input
            label="Password"
            type="password"
            placeholder="Your password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />

          <Button type="submit" fullWidth loading={login.isPending}>
            Sign in
          </Button>
        </form>

        <p className="mt-6 text-center text-body-sm text-text-tertiary">
          No account?{' '}
          <Link
            to="/signup"
            className="font-medium text-brand-400 hover:text-brand-300 transition-colors"
          >
            Sign up for free
          </Link>
        </p>
      </div>
    </div>
  );
}
