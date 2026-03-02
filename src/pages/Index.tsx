import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, GitBranch, MessageSquare, GitPullRequest, ArrowRight, Check,
  BarChart3, Users, Brain, TreePine, ChevronRight, Star, Github
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Brain,
    title: "RAG-Powered Chat",
    description: "Ask anything about your codebase. DevIntel retrieves the most relevant code chunks via vector search, giving AI precise context — not just a guess.",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  {
    icon: GitBranch,
    title: "Repository Intelligence",
    description: "Index your entire codebase using Tree-Sitter semantic chunking. Language-aware parsing preserves function and class boundaries for better results.",
    color: "text-green-400",
    bg: "bg-green-400/10",
  },
  {
    icon: GitPullRequest,
    title: "Autonomous PR Agent",
    description: "Describe a feature in plain English. DevIntel drafts a full PR with code changes, opens it for your review, and executes on your approval.",
    color: "text-purple-400",
    bg: "bg-purple-400/10",
  },
  {
    icon: BarChart3,
    title: "Usage Analytics",
    description: "Track query volume, token consumption, and your top repositories in real time. Know which repos your team relies on most.",
    color: "text-amber-400",
    bg: "bg-amber-400/10",
  },
  {
    icon: Users,
    title: "Organizations & Roles",
    description: "Create teams with Owner, Admin, and Member roles. Share indexed repositories across your organization with fine-grained access control.",
    color: "text-pink-400",
    bg: "bg-pink-400/10",
  },
  {
    icon: TreePine,
    title: "Smart Indexing",
    description: "Background Celery workers index repos asynchronously. Live progress bars keep you updated — no waiting for the page to respond.",
    color: "text-teal-400",
    bg: "bg-teal-400/10",
  },
];

const steps = [
  {
    num: "01",
    title: "Connect your repo",
    description: "Sign in with GitHub OAuth and pick any public or private repository. DevIntel connects in seconds with no config.",
  },
  {
    num: "02",
    title: "Index with one click",
    description: "A background worker clone and indexes your codebase using Tree-Sitter, building a vector database of semantic code chunks.",
  },
  {
    num: "03",
    title: "Chat, review, and ship",
    description: "Ask the AI anything, get code reviews with real diffs, or let the Autonomous PR Agent draft and open a pull request for you.",
  },
];

const pricingPlans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "For individual developers",
    features: ["3 repositories", "100 AI queries/month", "Basic PR reviews", "Diff viewer", "Community support"],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For teams and power users",
    features: [
      "Unlimited repositories",
      "Unlimited AI queries",
      "Autonomous PR Agent",
      "Organizations & Roles",
      "Real-time Analytics",
      "Priority support",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
];

const techStack = ["FastAPI", "PostgreSQL", "pgvector", "Redis", "OpenAI", "Tree-Sitter", "React", "Docker"];

// Animated terminal demo
const demoLines = [
  { delay: 0, text: "$ dev chat --repo josephkamau32/devintel", type: "cmd" },
  { delay: 0.8, text: '> "Explain the indexing pipeline"', type: "query" },
  { delay: 1.6, text: "Retrieving 6 relevant chunks via pgvector...", type: "info" },
  { delay: 2.4, text: "The indexing pipeline uses Tree-Sitter for", type: "response" },
  { delay: 2.7, text: "language-aware AST parsing. Each function and", type: "response" },
  { delay: 3.0, text: "class is chunked separately, then embedded", type: "response" },
  { delay: 3.3, text: "with text-embedding-3-small and stored in", type: "response" },
  { delay: 3.6, text: "pgvector for sub-50ms semantic search.", type: "response" },
  { delay: 4.2, text: "▋", type: "cursor" },
];

function TerminalDemo() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    const timers = demoLines.map((line, i) =>
      setTimeout(() => setVisibleCount(i + 1), line.delay * 1000)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="rounded-xl border border-border bg-[#0d1117] p-5 font-mono text-xs leading-relaxed shadow-2xl">
      <div className="mb-3 flex gap-1.5">
        <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
        <div className="h-2.5 w-2.5 rounded-full bg-amber-500/70" />
        <div className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
      </div>
      {demoLines.slice(0, visibleCount).map((line, i) => (
        <div
          key={i}
          className={
            line.type === "cmd" ? "text-green-400" :
              line.type === "query" ? "text-blue-400" :
                line.type === "info" ? "text-amber-400/80" :
                  line.type === "cursor" ? "text-foreground animate-pulse" :
                    "text-foreground/80"
          }
        >
          {line.text}
        </div>
      ))}
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Sticky Nav */}
      <nav className="fixed top-0 z-50 w-full border-b border-border/50 backdrop-blur-md bg-background/80">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">DevIntel AI</span>
          </Link>
          <div className="hidden items-center gap-6 sm:flex">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">How it works</a>
            <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Pricing</a>
            <Link to="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Log in</Link>
            <Link to="/signup"><Button size="sm">Get Started</Button></Link>
          </div>
          <Link to="/signup" className="sm:hidden"><Button size="sm">Get Started</Button></Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-24">
        <div className="absolute inset-0 dot-pattern opacity-40" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[600px] w-[800px] rounded-full bg-primary/5 blur-3xl -z-0" />

        <div className="relative mx-auto max-w-6xl px-6">
          <div className="grid gap-12 items-center lg:grid-cols-2">
            {/* Left: copy */}
            <div>
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <span className="inline-flex items-center rounded-full border border-border bg-accent px-3 py-1 text-xs text-muted-foreground">
                  <span className="mr-2 h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                  Now in public beta · Backed by OpenAI
                </span>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.5 }}
                className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl xl:text-6xl"
              >
                Your Codebase,{" "}
                <span className="bg-gradient-to-r from-blue-400 via-primary to-purple-500 bg-clip-text text-transparent">
                  Understood by AI
                </span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="mt-5 text-lg text-muted-foreground leading-relaxed"
              >
                Index any GitHub repo, chat with an AI that <em>actually</em> understands your code,
                get real diff-based PR reviews, and let the Autonomous Agent ship features for you.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.5 }}
                className="mt-8 flex flex-wrap gap-3"
              >
                <Link to="/signup">
                  <Button size="lg" className="gap-2">
                    Start for free <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <a href="https://github.com/josephkamau32/devintel" target="_blank" rel="noopener noreferrer">
                  <Button variant="outline" size="lg" className="gap-2">
                    <Github className="h-4 w-4" /> View on GitHub
                  </Button>
                </a>
              </motion.div>

              {/* Social proof */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.5 }}
                className="mt-8 flex items-center gap-4 text-xs text-muted-foreground"
              >
                <span className="flex items-center gap-1">
                  <Star className="h-3.5 w-3.5 text-amber-400" /> Open source
                </span>
                <span>·</span>
                <span>No credit card required</span>
                <span>·</span>
                <span>Free forever plan</span>
              </motion.div>
            </div>

            {/* Right: terminal */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <TerminalDemo />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tech stack strip */}
      <div className="border-y border-border bg-accent/30 py-4">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2">
            <p className="text-xs text-muted-foreground mr-2">Built with</p>
            {techStack.map(tech => (
              <span key={tech} className="text-xs text-muted-foreground">{tech}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Features */}
      <section id="features" className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl font-bold">Everything a developer needs</h2>
            <p className="mt-3 text-muted-foreground max-w-lg mx-auto">
              A complete AI coding copilot — from indexing to shipping. No more context switching.
            </p>
          </motion.div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feat, i) => (
              <motion.div
                key={feat.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.4 }}
                className="group rounded-xl border border-border bg-card p-6 transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${feat.bg}`}>
                  <feat.icon className={`h-5 w-5 ${feat.color}`} />
                </div>
                <h3 className="mt-4 font-semibold text-card-foreground">{feat.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{feat.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="border-t border-border py-24 bg-accent/20">
        <div className="mx-auto max-w-4xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl font-bold">Up and running in 3 steps</h2>
            <p className="mt-3 text-muted-foreground">No config, no DevOps. Just sign in and go.</p>
          </motion.div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative rounded-xl border border-border bg-card p-6"
              >
                <span className="text-4xl font-bold text-primary/20">{step.num}</span>
                <h3 className="mt-3 font-semibold text-card-foreground">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{step.description}</p>
                {i < steps.length - 1 && (
                  <ChevronRight className="absolute -right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground hidden md:block" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-border py-24">
        <div className="mx-auto max-w-4xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl font-bold">Simple pricing</h2>
            <p className="mt-3 text-muted-foreground">Start free, scale when you need more.</p>
          </motion.div>
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {pricingPlans.map((plan, i) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`rounded-xl border p-6 ${plan.highlighted
                  ? "border-primary bg-primary/5 shadow-lg shadow-primary/10"
                  : "border-border bg-card"
                  }`}
              >
                {plan.highlighted && (
                  <span className="inline-block rounded-full bg-primary px-2.5 py-0.5 text-[10px] font-semibold text-primary-foreground mb-3">
                    MOST POPULAR
                  </span>
                )}
                <h3 className="font-semibold text-card-foreground">{plan.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>
                <div className="mt-4">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-sm text-muted-foreground">{plan.period}</span>
                </div>
                <ul className="mt-6 space-y-2.5">
                  {plan.features.map(feat => (
                    <li key={feat} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-green-500 shrink-0" />
                      {feat}
                    </li>
                  ))}
                </ul>
                <Link to="/signup">
                  <Button className="mt-6 w-full" variant={plan.highlighted ? "default" : "outline"}>
                    {plan.cta}
                  </Button>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="border-t border-border py-20 bg-primary/5">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold">Ready to ship smarter?</h2>
            <p className="mt-4 text-muted-foreground">
              Join developers using DevIntel AI to understand codebases faster, review PRs deeper,
              and ship features without context-switching.
            </p>
            <Link to="/signup" className="mt-8 inline-block">
              <Button size="lg" className="gap-2">
                Get started for free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
              <Zap className="h-3 w-3 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">DevIntel AI</span>
          </div>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="https://github.com/josephkamau32/devintel" target="_blank" rel="noopener noreferrer"
              className="hover:text-foreground transition-colors flex items-center gap-1">
              <Github className="h-3.5 w-3.5" /> GitHub
            </a>
            <a href="#" className="hover:text-foreground transition-colors">Docs</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 DevIntel AI. MIT License.</p>
        </div>
      </footer>
    </div>
  );
}
