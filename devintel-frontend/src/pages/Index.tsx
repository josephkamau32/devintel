import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Zap, GitBranch, MessageSquare, GitPullRequest, ArrowRight, Check, Search, Bot, Code2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: GitBranch,
    title: "Repository Intelligence",
    description: "Index your entire codebase and get instant insights into architecture, patterns, and dependencies.",
  },
  {
    icon: MessageSquare,
    title: "AI Code Assistant",
    description: "Chat with an AI that deeply understands your code. Get explanations, find bugs, and refactor confidently.",
  },
  {
    icon: GitPullRequest,
    title: "Pull Request Review AI",
    description: "Automated PR reviews with actionable suggestions, security checks, and code quality analysis.",
  },
];

const pricingPlans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "For individual developers",
    features: ["3 repositories", "50 AI queries/month", "Basic PR reviews", "Community support"],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For teams and power users",
    features: ["Unlimited repositories", "Unlimited AI queries", "Advanced PR reviews", "Priority support", "Custom integrations", "Team collaboration"],
    cta: "Start Free Trial",
    highlighted: true,
  },
];

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="fixed top-0 z-50 w-full border-b border-border/50 glass">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">DevIntel AI</span>
          </Link>
          <div className="hidden items-center gap-6 sm:flex">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Pricing</a>
            <Link to="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Log in</Link>
            <Link to="/signup">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-20">
        <div className="absolute inset-0 dot-pattern opacity-50" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-primary/5 blur-3xl" />
        <div className="relative mx-auto max-w-4xl px-6 text-center">
          <motion.div {...fadeUp}>
            <span className="inline-flex items-center rounded-full border border-border bg-accent px-3 py-1 text-xs text-muted-foreground">
              <span className="mr-2 h-1.5 w-1.5 rounded-full bg-success animate-pulse-slow" />
              Now in public beta
            </span>
          </motion.div>
          <motion.h1
            {...fadeUp}
            transition={{ delay: 0.1, duration: 0.5 }}
            className="mt-6 text-4xl font-bold tracking-tight sm:text-6xl"
          >
            Understand Your Codebase{" "}
            <span className="gradient-text">Instantly with AI</span>
          </motion.h1>
          <motion.p
            {...fadeUp}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground"
          >
            Connect your GitHub repo and get contextual AI insights, refactoring suggestions, and intelligent code explanations.
          </motion.p>
          <motion.div
            {...fadeUp}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="mt-8 flex items-center justify-center gap-4"
          >
            <Link to="/signup">
              <Button size="lg" className="gap-2">
                Get Started <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button variant="outline" size="lg">
                View Demo
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-t border-border py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold">How It Works</h2>
            <p className="mt-3 text-muted-foreground">Four steps from connection to autonomous code fixes.</p>
          </div>
          <div className="mt-12 grid gap-1 md:grid-cols-4">
            {[
              { step: "1", icon: GitBranch, title: "Connect", desc: "Authenticate with GitHub OAuth and select your repositories." },
              { step: "2", icon: Code2, title: "Index", desc: "AST-aware Tree-Sitter chunking creates semantic embeddings via pgvector." },
              { step: "3", icon: Search, title: "Chat & Review", desc: "RAG-powered conversations and AI pull request reviews." },
              { step: "4", icon: Bot, title: "Auto-Fix", desc: "Agent creates a branch, commits fixes, and opens a PR automatically." },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.4 }}
                className="relative flex flex-col items-center text-center p-6"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary border border-primary/20">
                  <item.icon className="h-5 w-5" />
                </div>
                <span className="mt-1 text-xs font-medium text-primary">Step {item.step}</span>
                <h3 className="mt-2 font-semibold text-card-foreground">{item.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
                {i < 3 && <div className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 text-muted-foreground/30"><ArrowRight className="h-5 w-5" /></div>}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-border py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold">Built for developers</h2>
            <p className="mt-3 text-muted-foreground">Everything you need to understand and improve your codebase.</p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                className="group rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/30"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold text-card-foreground">{feature.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-border py-20">
        <div className="mx-auto max-w-4xl px-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold">Simple pricing</h2>
            <p className="mt-3 text-muted-foreground">Start free, upgrade when you need more.</p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {pricingPlans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-xl border p-6 ${plan.highlighted
                  ? "border-primary bg-card glow-primary"
                  : "border-border bg-card"
                  }`}
              >
                <h3 className="font-semibold text-card-foreground">{plan.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>
                <div className="mt-4">
                  <span className="text-3xl font-bold text-card-foreground">{plan.price}</span>
                  <span className="text-sm text-muted-foreground">{plan.period}</span>
                </div>
                <ul className="mt-6 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-success" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link to="/signup">
                  <Button
                    className="mt-6 w-full"
                    variant={plan.highlighted ? "default" : "outline"}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
              <Zap className="h-3 w-3 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">DevIntel AI</span>
          </div>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="https://github.com/josephkamau32/devintel" target="_blank" rel="noopener noreferrer" className="hover:text-foreground transition-colors">GitHub</a>
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#pricing" className="hover:text-foreground transition-colors">Pricing</a>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 DevIntel AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
