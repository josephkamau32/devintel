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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">Overview of your DevIntel AI workspace</p>
        </div>
        <StatusBadge status="All systems operational" variant="success" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Activity Feed */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold text-card-foreground">Recent Activity</h2>
          <div className="mt-4 space-y-3">
            {mockActivities.map((item) => (
              <div key={item.id} className="flex items-start gap-3 rounded-lg p-2 hover:bg-accent transition-colors">
                <span className="text-base">{typeIcons[item.type]}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-card-foreground">{item.message}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{item.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold text-card-foreground">Quick Actions</h2>
          <div className="mt-4 space-y-3">
            <Link to="/repositories">
              <Button variant="outline" className="w-full justify-between">
                <span className="flex items-center gap-2"><Plus className="h-4 w-4" /> Index New Repository</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/chat">
              <Button variant="outline" className="w-full justify-between">
                <span className="flex items-center gap-2"><Zap className="h-4 w-4" /> Start AI Chat</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/pull-requests">
              <Button variant="outline" className="w-full justify-between">
                <span className="flex items-center gap-2"><GitPullRequest className="h-4 w-4" /> Review Pull Requests</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
