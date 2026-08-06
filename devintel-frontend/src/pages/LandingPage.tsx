import { Link } from 'react-router-dom';
import { useDemoLogin } from '../hooks/useAuth';
import { useState, useEffect, useRef } from 'react';
import {
  Code2,
  MessageSquareText,
  ShieldCheck,
  BarChart3,
  Zap,
  Lock,
  RefreshCw,
  ArrowRight,
  Play,
  ExternalLink,
  Server,
  Monitor,
  Puzzle,
  Github,
} from 'lucide-react';

/* ─── Data ─── */

const features = [
  {
    icon: MessageSquareText,
    title: 'RAG-Powered Chat',
    desc: 'Ask natural language questions about your codebase — backed by pgvector semantic search with AST-aware chunking.',
  },
  {
    icon: ShieldCheck,
    title: 'AI Code Review',
    desc: 'Automated PR reviews with severity-tagged issues, security analysis, and actionable improvement suggestions.',
  },
  {
    icon: BarChart3,
    title: 'Code Health Scoring',
    desc: 'Multi-dimensional quality analysis — complexity, documentation, maintainability, test coverage, and security.',
  },
  {
    icon: Zap,
    title: 'Autonomous Agent',
    desc: 'Instruct the AI to implement features — it drafts a plan, creates a branch, commits code, and opens a PR.',
  },
  {
    icon: Lock,
    title: 'Enterprise Security',
    desc: 'JWT + HttpOnly cookies, Fernet AES-256 token encryption, OWASP headers, CSRF protection, audit logging.',
  },
  {
    icon: RefreshCw,
    title: 'Resilience Patterns',
    desc: 'Circuit breaker, exponential backoff retries, retry queues, Redis caching — production-grade infrastructure.',
  },
];

const techStack = [
  'FastAPI',
  'React 18',
  'TypeScript',
  'PostgreSQL + pgvector',
  'OpenAI GPT-4o',
  'Redis',
  'Docker',
  'SQLAlchemy',
];

const stats = [
  { value: '17+', label: 'Database Tables' },
  { value: '24', label: 'Service Modules' },
  { value: '20', label: 'DB Migrations' },
  { value: '6', label: 'Docker Services' },
];

const architecture = [
  {
    icon: Server,
    name: 'Backend API',
    tech: 'FastAPI + PostgreSQL + pgvector',
    desc: '24 service modules, circuit breaker, retry queues',
  },
  {
    icon: Monitor,
    name: 'Dashboard',
    tech: 'React 18 + TypeScript + Vite',
    desc: 'RAG chat, code health analytics, PR reviews',
  },
  {
    icon: Puzzle,
    name: 'VS Code Extension',
    tech: 'TypeScript + Webpack',
    desc: 'Sidebar chat, file review, secure token storage',
  },
];

/* ─── Intersection Observer hook ─── */

function useInView(threshold = 0.15) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, inView };
}

/* ─── Component ─── */

export function LandingPage() {
  const demoLogin = useDemoLogin();
  const featuresSection = useInView();
  const archSection = useInView();
  const ctaSection = useInView();

  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      {/* Subtle background pattern */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage:
              'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.5) 1px, transparent 0)',
            backgroundSize: '32px 32px',
          }}
        />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[600px] w-[800px] rounded-full bg-brand-600/5 blur-[150px]" />
      </div>

      {/* ─── Navigation ─── */}
      <nav className="relative z-10 border-b border-border">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600">
              <Code2 className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold tracking-tight">DevIntel</span>
          </div>
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/josephkamau32/devintel"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-text-tertiary transition-colors hover:text-text-secondary hover:bg-surface-3"
            >
              <Github className="h-4 w-4" />
              GitHub
            </a>
            <Link
              to="/login"
              className="rounded-md px-3 py-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary hover:bg-surface-3"
            >
              Sign in
            </Link>
            <Link
              to="/signup"
              className="rounded-lg bg-brand-600 px-3.5 py-1.5 text-sm font-medium text-white shadow-subtle transition-all hover:bg-brand-500 hover:shadow-medium"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section className="relative z-10 mx-auto max-w-3xl px-4 pb-16 pt-20 text-center sm:px-6 sm:pt-28">
        <div className="animate-fade-in">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border-medium bg-surface-2 px-3.5 py-1 text-xs font-medium text-text-secondary">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-status-success opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-status-success" />
            </span>
            Open Source · Built with GPT-4o + RAG
          </div>
        </div>

        <h1 className="animate-slide-up text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-display">
          Developer intelligence{' '}
          <br className="hidden sm:block" />
          for your{' '}
          <span className="text-gradient">GitHub codebase</span>
        </h1>

        <p
          className="mx-auto mt-5 max-w-xl text-body text-text-secondary animate-slide-up"
          style={{ animationDelay: '80ms' }}
        >
          Index your repositories, chat with your code using RAG, review pull
          requests with AI, score code health, and generate auto-fix PRs — all
          with production-grade security and enterprise resilience patterns.
        </p>

        <div
          className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row animate-slide-up"
          style={{ animationDelay: '160ms' }}
        >
          <button
            onClick={() => demoLogin.mutate()}
            disabled={demoLogin.isPending}
            className="group flex items-center gap-2.5 rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white shadow-subtle transition-all hover:bg-brand-500 hover:shadow-medium disabled:opacity-50"
          >
            {demoLogin.isPending ? (
              <div className="h-4 w-4 animate-spin-slow rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Try Live Demo
          </button>

          <Link
            to="/signup"
            className="group flex items-center gap-2 rounded-lg border border-border-medium px-5 py-2.5 text-sm font-medium text-text-secondary transition-all hover:text-text-primary hover:bg-surface-3 hover:border-border-strong"
          >
            Create free account
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        <p
          className="mt-4 text-xs text-text-quaternary animate-slide-up"
          style={{ animationDelay: '240ms' }}
        >
          No credit card required · Demo available instantly
        </p>
      </section>

      {/* ─── Stats ─── */}
      <section className="relative z-10 border-y border-border">
        <div className="mx-auto grid max-w-3xl grid-cols-2 gap-6 px-4 py-10 sm:grid-cols-4 sm:px-6">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-bold text-text-primary">
                {stat.value}
              </div>
              <div className="mt-0.5 text-overline uppercase text-text-quaternary">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Features ─── */}
      <section
        ref={featuresSection.ref}
        className="relative z-10 mx-auto max-w-5xl px-4 py-20 sm:px-6"
      >
        <div className="mb-12 text-center">
          <h2 className="text-h1 text-text-primary">
            Enterprise-grade AI code intelligence
          </h2>
          <p className="mt-3 text-body text-text-secondary max-w-lg mx-auto">
            Beyond simple ChatGPT wrappers — a complete RAG pipeline with
            production resilience patterns.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className={`group card-interactive p-5 transition-all duration-300 ${
                  featuresSection.inView
                    ? 'opacity-100 translate-y-0'
                    : 'opacity-0 translate-y-3'
                }`}
                style={{
                  transitionDelay: featuresSection.inView
                    ? `${i * 60}ms`
                    : '0ms',
                }}
              >
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-surface-4 text-text-secondary group-hover:text-brand-400 transition-colors">
                  <Icon className="h-[18px] w-[18px]" />
                </div>
                <h3 className="mb-1.5 text-sm font-semibold text-text-primary">
                  {f.title}
                </h3>
                <p className="text-body-sm text-text-tertiary leading-relaxed">
                  {f.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ─── Architecture ─── */}
      <section
        ref={archSection.ref}
        className="relative z-10 border-y border-border py-20"
      >
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          <div className="mb-10 text-center">
            <h3 className="text-h2 text-text-primary">Built for production</h3>
            <p className="mt-2 text-body text-text-secondary max-w-md mx-auto">
              Three integrated subsystems working together — backend API, React
              dashboard, and VS Code extension.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {architecture.map((item, i) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.name}
                  className={`card-interactive p-5 transition-all duration-300 ${
                    archSection.inView
                      ? 'opacity-100 translate-y-0'
                      : 'opacity-0 translate-y-3'
                  }`}
                  style={{
                    transitionDelay: archSection.inView
                      ? `${i * 80}ms`
                      : '0ms',
                  }}
                >
                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-surface-4 text-text-secondary">
                    <Icon className="h-[18px] w-[18px]" />
                  </div>
                  <h4 className="text-sm font-semibold text-text-primary mb-1">
                    {item.name}
                  </h4>
                  <p className="text-xs font-medium text-brand-400 mb-1.5">
                    {item.tech}
                  </p>
                  <p className="text-body-sm text-text-quaternary">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── Tech Stack ─── */}
      <section className="relative z-10 py-14">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <p className="mb-6 text-overline uppercase text-text-quaternary">
            Built with
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {techStack.map((t) => (
              <span
                key={t}
                className="rounded-md border border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-text-tertiary"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section
        ref={ctaSection.ref}
        className="relative z-10 border-t border-border py-20"
      >
        <div
          className={`mx-auto max-w-lg px-4 text-center sm:px-6 transition-all duration-500 ${
            ctaSection.inView
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 translate-y-4'
          }`}
        >
          <h2 className="text-h1 text-text-primary mb-3">
            Ready to understand your codebase?
          </h2>
          <p className="text-body text-text-secondary mb-8">
            Start chatting with your code in under a minute. No credit card
            required.
          </p>
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => demoLogin.mutate()}
              disabled={demoLogin.isPending}
              className="flex items-center gap-2 rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white shadow-subtle transition-all hover:bg-brand-500 hover:shadow-medium disabled:opacity-50"
            >
              {demoLogin.isPending ? (
                <div className="h-4 w-4 animate-spin-slow rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {demoLogin.isPending ? 'Loading…' : 'Try the demo'}
            </button>
            <Link
              to="/signup"
              className="flex items-center gap-2 rounded-lg border border-border-medium px-5 py-2.5 text-sm font-medium text-text-secondary transition-all hover:text-text-primary hover:bg-surface-3"
            >
              Create account
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="relative z-10 border-t border-border py-6">
        <div className="mx-auto max-w-6xl px-4 flex flex-col items-center gap-3 sm:flex-row sm:justify-between sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-brand-600/60">
              <Code2 className="h-3 w-3 text-white" />
            </div>
            <span className="text-xs text-text-quaternary">
              DevIntel — Open source AI code intelligence
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-text-quaternary">
            <a
              href="https://github.com/josephkamau32/devintel"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-tertiary transition-colors inline-flex items-center gap-1"
            >
              <ExternalLink className="h-3 w-3" />
              GitHub
            </a>
            <span className="text-border-strong">·</span>
            <span>MIT License</span>
            <span className="text-border-strong">·</span>
            <span>Built by Joseph Kamau</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
