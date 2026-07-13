import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useSignup, useDemoLogin } from '../hooks/useAuth';

export function SignupPage() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const signup = useSignup();
  const demoLogin = useDemoLogin();

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!form.email) newErrors.email = 'Email is required';
    if (!form.password) newErrors.password = 'Password is required';
    if (form.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(form.password)) newErrors.password = 'Must include an uppercase letter';
    if (!/[0-9]/.test(form.password)) newErrors.password = 'Must include a number';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    signup.mutate({
      email: form.email,
      password: form.password,
      full_name: form.full_name || undefined,
    });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
            <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="mt-1 text-sm text-slate-400">Start understanding your codebase with AI</p>
        </div>

        <button
          onClick={() => demoLogin.mutate()}
          disabled={demoLogin.isPending}
          className="mb-4 flex w-full items-center justify-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-sm font-medium text-emerald-400 transition hover:bg-emerald-500/20 disabled:opacity-50"
        >
          {demoLogin.isPending ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          Try Demo — No account needed
        </button>

        <a
          href={`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api/v1/auth/github`}
          className="mb-4 flex w-full items-center justify-center gap-3 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 .5C5.648.5.5 5.648.5 12c0 5.085 3.292 9.387 7.863 10.91.575.106.786-.25.786-.555 0-.274-.01-1-.015-1.964-3.198.695-3.874-1.542-3.874-1.542-.523-1.33-1.277-1.684-1.277-1.684-1.044-.713.08-.699.08-.699 1.154.082 1.762 1.187 1.762 1.187 1.026 1.758 2.691 1.25 3.347.956.104-.744.402-1.25.73-1.537-2.553-.29-5.237-1.276-5.237-5.682 0-1.256.448-2.283 1.185-3.087-.12-.29-.515-1.46.112-3.046 0 0 .967-.31 3.167 1.18A11.01 11.01 0 0 1 12 6.42c.98.005 1.966.133 2.887.39 2.197-1.49 3.163-1.18 3.163-1.18.628 1.586.233 2.756.114 3.046.738.804 1.184 1.831 1.184 3.087 0 4.417-2.688 5.39-5.25 5.674.414.355.782 1.058.782 2.133 0 1.54-.014 2.781-.014 3.16 0 .307.208.666.79.553C20.21 21.383 23.5 17.083 23.5 12 23.5 5.648 18.352.5 12 .5Z"/>
          </svg>
          Continue with GitHub
        </a>

        <div className="relative mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <div className="relative flex justify-center text-xs text-slate-500">
            <span className="bg-slate-950 px-3">or sign up with email</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Full name"
            type="text"
            placeholder="Jane Smith"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
          <Input
            label="Email"
            type="email"
            placeholder="jane@company.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            error={errors.email}
            required
          />
          <Input
            label="Password"
            type="password"
            placeholder="Min. 8 chars, 1 uppercase, 1 number"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            error={errors.password}
            required
          />

          <Button type="submit" fullWidth loading={signup.isPending}>
            Create account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-violet-400 hover:text-violet-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
