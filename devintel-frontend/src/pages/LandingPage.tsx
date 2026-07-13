import { Link } from 'react-router-dom';
import { useDemoLogin } from '../hooks/useAuth';

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

export function LandingPage() {
  const demoLogin = useDemoLogin();

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Gradient background effect */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-1/2 left-1/2 h-[800px] w-[800px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[600px] w-[600px] rounded-full bg-indigo-600/8 blur-[100px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-slate-800/50 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-600">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <span className="text-lg font-semibold text-white">DevIntel AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition hover:text-white"
            >
              Sign in
            </Link>
            <Link
              to="/signup"
              className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-violet-500"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-4xl px-6 pb-20 pt-24 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-300">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Open Source · Built with GPT-4o + RAG
        </div>

        <h1 className="text-5xl font-bold leading-tight tracking-tight text-white sm:text-6xl">
          AI coding assistant for your{' '}
          <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
            GitHub codebase
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-400">
          Index your repositories, chat with your code using RAG, review pull requests with AI,
          score code health, and generate auto-fix PRs — all with production-grade security
          and enterprise resilience patterns.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <button
            onClick={() => demoLogin.mutate()}
            disabled={demoLogin.isPending}
            className="group flex items-center gap-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:shadow-xl hover:shadow-violet-500/30 disabled:opacity-50"
          >
            {demoLogin.isPending ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <svg className="h-5 w-5 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            Try Live Demo
          </button>

          <Link
            to="/signup"
            className="flex items-center gap-2 rounded-xl border border-slate-700 px-7 py-3.5 text-sm font-semibold text-slate-200 transition hover:border-slate-600 hover:bg-slate-800/50"
          >
            Create free account
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>

        <p className="mt-4 text-xs text-slate-500">
          No credit card required · Demo available instantly
        </p>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-24">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-bold text-white">Enterprise-grade AI code intelligence</h2>
          <p className="mt-3 text-slate-400">
            Beyond simple ChatGPT wrappers — a complete RAG pipeline with production resilience patterns.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="group rounded-2xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:border-slate-700 hover:bg-slate-900/80"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600/10 text-violet-400 transition group-hover:bg-violet-600/20">
                {f.icon}
              </div>
              <h3 className="mb-2 text-lg font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="relative z-10 border-t border-slate-800/50 py-16">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h3 className="mb-8 text-sm font-medium uppercase tracking-wider text-slate-500">Built with</h3>
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4">
            {techStack.map((t) => (
              <span
                key={t.name}
                className={`text-sm font-medium ${t.color} opacity-70 transition hover:opacity-100`}
              >
                {t.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/50 py-8">
        <div className="mx-auto max-w-6xl px-6 text-center text-xs text-slate-500">
          <p>
            DevIntel AI — Open source AI code intelligence platform.{' '}
            <a
              href="https://github.com/josephkamau32/devintel"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 underline-offset-2 hover:text-violet-400 hover:underline"
            >
              View on GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
