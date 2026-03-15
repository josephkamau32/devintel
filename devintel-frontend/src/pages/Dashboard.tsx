import { GitBranch, MessageSquare, GitPullRequest, Activity, ArrowRight, Plus, Zap } from "lucide-react";
import { StatCard } from "@/components/shared/StatCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { mockActivities } from "@/lib/mock-data";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const stats = [
  { title: "Repositories Indexed", value: 5, icon: GitBranch, trend: { value: "+2 this week", positive: true } },
  { title: "AI Queries This Month", value: 48, icon: MessageSquare, subtitle: "50 limit on Free plan" },
  { title: "PRs Analyzed", value: 23, icon: GitPullRequest, trend: { value: "+8 this week", positive: true } },
  { title: "System Status", value: "Operational", icon: Activity },
];

const typeIcons: Record<string, string> = {
  index: "📦",
  chat: "💬",
  pr_review: "🔍",
  alert: "⚠️",
};

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground/80">Overview of your DevIntel AI workspace</p>
        </div>
        <StatusBadge status="All systems operational" variant="success" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <StatCard key={stat.title} {...stat} delay={i * 100} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Activity Feed */}
        <div className="lg:col-span-2 glass-card rounded-xl p-5 animate-slide-up" style={{ animationDelay: '300ms', animationFillMode: 'both' }}>
          <h2 className="font-semibold text-foreground flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Recent Activity
          </h2>
          <div className="mt-4 space-y-3">
            {mockActivities.map((item) => (
              <div key={item.id} className="group flex items-start gap-4 rounded-lg p-3 hover:bg-white/5 transition-all duration-300 border border-transparent hover:border-border/30">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-card border border-border/50 text-base shadow-sm group-hover:scale-110 group-hover:bg-primary/10 transition-all duration-300">
                  {typeIcons[item.type]}
                </div>
                <div className="flex-1 min-w-0 py-1">
                  <p className="text-sm font-medium text-foreground">{item.message}</p>
                  <p className="mt-1 text-xs text-muted-foreground group-hover:text-primary/70 transition-colors">{item.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="glass-card rounded-xl p-5 animate-slide-up" style={{ animationDelay: '400ms', animationFillMode: 'both' }}>
          <h2 className="font-semibold text-foreground flex items-center gap-2">
            <Zap className="h-5 w-5 text-secondary" />
            Quick Actions
          </h2>
          <div className="mt-5 space-y-3">
            <Link to="/repositories">
              <Button variant="outline" className="w-full justify-between h-12 bg-card/50 hover:bg-white/10 border-border/50 hover:border-primary/50 transition-all duration-300 group">
                <span className="flex items-center gap-2 text-muted-foreground group-hover:text-foreground transition-colors"><Plus className="h-4 w-4 text-primary" /> Index New Repository</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
              </Button>
            </Link>
            <Link to="/chat">
              <Button variant="outline" className="w-full justify-between h-12 bg-card/50 hover:bg-white/10 border-border/50 hover:border-secondary/50 transition-all duration-300 group">
                <span className="flex items-center gap-2 text-muted-foreground group-hover:text-foreground transition-colors"><Zap className="h-4 w-4 text-secondary" /> Start AI Chat</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-secondary group-hover:translate-x-1 transition-all" />
              </Button>
            </Link>
            <Link to="/pull-requests">
              <Button variant="outline" className="w-full justify-between h-12 bg-card/50 hover:bg-white/10 border-border/50 hover:border-success/50 transition-all duration-300 group">
                <span className="flex items-center gap-2 text-muted-foreground group-hover:text-foreground transition-colors"><GitPullRequest className="h-4 w-4 text-success" /> Review Pull Requests</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-success group-hover:translate-x-1 transition-all" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
