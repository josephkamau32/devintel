import { Link } from 'react-router-dom';
import { useDemoLogin } from '../hooks/useAuth';
import { useState, useEffect } from 'react';

const features = [
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
    title: 'RAG-Powered Chat',
    desc: 'Ask natural language questions about your codebase — backed by pgvector semantic search with AST-aware chunking.',
    gradient: 'from-violet-500/20 to-purple-500/20',
    iconColor: 'text-violet-400',
    borderHover: 'hover:border-violet-500/30',
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    title: 'AI Code Review',
    desc: 'Automated PR reviews with severity-tagged issues, security analysis, and actionable improvement suggestions.',
    gradient: 'from-emerald-500/20 to-teal-500/20',
    iconColor: 'text-emerald-400',
    borderHover: 'hover:border-emerald-500/30',
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: 'Code Health Scoring',
    desc: 'Multi-dimensional quality analysis — complexity, documentation, maintainability, test coverage, and security.',
    gradient: 'from-sky-500/20 to-blue-500/20',
    iconColor: 'text-sky-400',
    borderHover: 'hover:border-sky-500/30',
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: 'Autonomous Agent',
    desc: 'Instruct the AI to implement features — it drafts a plan, creates a branch, commits code, and opens a PR.',
    gradient: 'from-amber-500/20 to-orange-500/20',
    iconColor: 'text-amber-400',
    borderHover: 'hover:border-amber-500/30',
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    title: 'Enterprise Security',
    desc: 'JWT + HttpOnly cookies, Fernet AES-256 token encryption, OWASP headers, CSRF protection, audit logging.',
    gradient: 'from-rose-500/20 to-pink-500/20',
    iconColor: 'text-rose-400',
    borderHover: 'hover:border-rose-500/30',
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    title: 'Resilience Patterns',
    desc: 'Circuit breaker, exponential backoff retries, retry queues, Redis caching — production-grade infrastructure.',
    gradient: 'from-indigo-500/20 to-violet-500/20',
    iconColor: 'text-indigo-400',
    borderHover: 'hover:border-indigo-500/30',
  },
];

const techStack = [
  { name: 'FastAPI', color: 'text-emerald-400' },
  { name: 'React 18', color: 'text-sky-400' },
  { name: 'TypeScript', color: 'text-blue-400' },
  { name: 'PostgreSQL + pgvector', color: 'text-indigo-400' },
  { name: 'OpenAI GPT-4o', color: 'text-purple-400' },
  { name: 'Redis', color: 'text-red-400' },
  { name: 'Docker', color: 'text-cyan-400' },
  { name: 'SQLAlchemy', color: 'text-amber-400' },
];

const stats = [
  { value: '17+', label: 'Database Tables' },
  { value: '24', label: 'Service Modules' },
  { value: '20', label: 'DB Migrations' },
  { value: '6', label: 'Docker Services' },
];

export function LandingPage() {
  const demoLogin = useDemoLogin();
  const [visibleFeatures, setVisibleFeatures] = useState<number[]>([]);

  // Staggered feature reveal animation
  useEffect(() => {
    features.forEach((_, i) => {
      setTimeout(() => {
        setVisibleFeatures((prev) => [...prev, i]);
      }, 150 * i + 600);
    });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Animated gradient background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-1/2 left-1/2 h-[900px] w-[900px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-[140px] animate-pulse-slow" />
        <div className="absolute bottom-0 right-0 h-[700px] w-[700px] rounded-full bg-indigo-600/8 blur-[120px] animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/3 left-0 h-[400px] w-[400px] rounded-full bg-purple-600/5 blur-[100px] animate-pulse-slow" style={{ animationDelay: '3s' }} />
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-[0.015]" style={{
          backgroundImage: 'linear-gradient(rgba(148,163,184,1) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,1) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-slate-800/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 shadow-lg shadow-violet-500/20">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <span className="text-lg font-bold text-white tracking-tight">DevIntel AI</span>
          </div>
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/josephkamau32/devintel"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:text-white hover:bg-slate-800/50"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 .5C5.648.5.5 5.648.5 12c0 5.085 3.292 9.387 7.863 10.91.575.106.786-.25.786-.555 0-.274-.01-1-.015-1.964-3.198.695-3.874-1.542-3.874-1.542-.523-1.33-1.277-1.684-1.277-1.684-1.044-.713.08-.699.08-.699 1.154.082 1.762 1.187 1.762 1.187 1.026 1.758 2.691 1.25 3.347.956.104-.744.402-1.25.73-1.537-2.553-.29-5.237-1.276-5.237-5.682 0-1.256.448-2.283 1.185-3.087-.12-.29-.515-1.46.112-3.046 0 0 .967-.31 3.167 1.18A11.01 11.01 0 0 1 12 6.42c.98.005 1.966.133 2.887.39 2.197-1.49 3.163-1.18 3.163-1.18.628 1.586.233 2.756.114 3.046.738.804 1.184 1.831 1.184 3.087 0 4.417-2.688 5.39-5.25 5.674.414.355.782 1.058.782 2.133 0 1.54-.014 2.781-.014 3.16 0 .307.208.666.79.553C20.21 21.383 23.5 17.083 23.5 12 23.5 5.648 18.352.5 12 .5Z"/>
              </svg>
              GitHub
            </a>
            <Link
              to="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition hover:text-white hover:bg-slate-800/50"
            >
              Sign in
            </Link>
            <Link
              to="/signup"
              className="rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-violet-500/20 transition hover:shadow-xl hover:shadow-violet-500/30 hover:brightness-110"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-4xl px-6 pb-20 pt-20 text-center sm:pt-28">
        <div className="animate-fade-in">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-300 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            Open Source · Built with GPT-4o + RAG
          </div>
        </div>

        <h1 className="animate-slide-up text-5xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-6xl lg:text-7xl">
          AI coding assistant{' '}
          <br className="hidden sm:block" />
          for your{' '}
          <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent animate-gradient">
            GitHub codebase
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-400 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          Index your repositories, chat with your code using RAG, review pull requests with AI,
          score code health, and generate auto-fix PRs — all with production-grade security
          and enterprise resilience patterns.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <button
            onClick={() => demoLogin.mutate()}
            disabled={demoLogin.isPending}
            className="group relative flex items-center gap-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-violet-500/40 hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
          >
            {/* Shimmer overlay */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            {demoLogin.isPending ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <svg className="h-5 w-5 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            <span className="relative">Try Live Demo</span>
          </button>

          <Link
            to="/signup"
            className="group flex items-center gap-2 rounded-xl border border-slate-700 px-8 py-4 text-sm font-semibold text-slate-200 transition-all duration-300 hover:border-slate-500 hover:bg-slate-800/50 hover:scale-[1.02]"
          >
            Create free account
            <svg className="h-4 w-4 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>

        <p className="mt-5 text-xs text-slate-500 animate-slide-up" style={{ animationDelay: '0.3s' }}>
          No credit card required · Demo available instantly
        </p>
      </section>

      {/* Stats bar */}
      <section className="relative z-10 border-y border-slate-800/50 bg-slate-900/30 backdrop-blur-sm">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-6 px-6 py-10 sm:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold bg-gradient-to-b from-white to-slate-400 bg-clip-text text-transparent">
                {stat.value}
              </div>
              <div className="mt-1 text-xs font-medium text-slate-500 uppercase tracking-wider">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Enterprise-grade AI code intelligence
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
            Beyond simple ChatGPT wrappers — a complete RAG pipeline with production resilience patterns.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div
              key={f.title}
              className={`group relative rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 transition-all duration-500 ${f.borderHover} hover:bg-slate-900/70 hover:-translate-y-1 hover:shadow-lg ${
                visibleFeatures.includes(i)
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-4'
              }`}
              style={{ transitionDelay: `${i * 50}ms` }}
            >
              {/* Gradient overlay on hover */}
              <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${f.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              
              <div className="relative">
                <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-slate-800/80 ${f.iconColor} transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg`}>
                  {f.icon}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">{f.title}</h3>
                <p className="text-sm leading-relaxed text-slate-400 group-hover:text-slate-300 transition-colors">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture preview */}
      <section className="relative z-10 border-y border-slate-800/50 bg-slate-900/20 py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h3 className="mb-4 text-2xl font-bold text-white">Built for production</h3>
          <p className="mb-10 text-slate-400 max-w-xl mx-auto">
            Three integrated subsystems working together — backend API, React dashboard, and VS Code extension.
          </p>
          
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { name: 'Backend API', tech: 'FastAPI + PostgreSQL + pgvector', icon: '⚡', desc: '24 service modules, circuit breaker, retry queues' },
              { name: 'Dashboard', tech: 'React 18 + TypeScript + Vite', icon: '🎨', desc: 'RAG chat, code health analytics, PR reviews' },
              { name: 'VS Code Extension', tech: 'TypeScript + Webpack', icon: '🧩', desc: 'Sidebar chat, file review, secure token storage' },
            ].map((item) => (
              <div key={item.name} className="group rounded-xl border border-slate-800 bg-slate-900/50 p-5 text-left transition-all hover:border-slate-700 hover:bg-slate-900/80">
                <div className="mb-3 text-2xl">{item.icon}</div>
                <h4 className="mb-1 text-sm font-semibold text-white">{item.name}</h4>
                <p className="mb-2 text-xs text-violet-400 font-medium">{item.tech}</p>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="relative z-10 py-16">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h3 className="mb-8 text-sm font-medium uppercase tracking-widest text-slate-500">Built with</h3>
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4">
            {techStack.map((t) => (
              <span
                key={t.name}
                className={`text-sm font-medium ${t.color} opacity-60 transition-all duration-300 hover:opacity-100 hover:scale-110 cursor-default`}
              >
                {t.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-20">
        <div className="mx-auto max-w-2xl px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to understand your codebase?</h2>
          <p className="text-slate-400 mb-8">
            Start chatting with your code in under a minute. No credit card required.
          </p>
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => demoLogin.mutate()}
              disabled={demoLogin.isPending}
              className="rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:shadow-xl hover:shadow-violet-500/40 hover:scale-[1.02] disabled:opacity-50"
            >
              {demoLogin.isPending ? 'Loading…' : 'Try the demo'}
            </button>
            <Link
              to="/signup"
              className="rounded-xl border border-slate-700 px-8 py-3.5 text-sm font-semibold text-slate-200 transition-all hover:border-slate-500 hover:bg-slate-800/50"
            >
              Create account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/50 py-8">
        <div className="mx-auto max-w-6xl px-6 flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-violet-600/50">
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <span className="text-xs text-slate-500">DevIntel AI — Open source AI code intelligence</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <a
              href="https://github.com/josephkamau32/devintel"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-violet-400 transition-colors"
            >
              GitHub
            </a>
            <span className="text-slate-700">·</span>
            <span>MIT License</span>
            <span className="text-slate-700">·</span>
            <span>Built by Joseph Kamau</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
