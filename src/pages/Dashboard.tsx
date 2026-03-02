import { useState, useEffect } from "react";
import { GitBranch, MessageSquare, GitPullRequest, Activity, ArrowRight, Plus, Zap, Loader2 } from "lucide-react";
import { StatCard } from "@/components/shared/StatCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type { Repository, AnalyticsDashboard } from "@/lib/types";

export default function DashboardPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [repoData, analyticsData] = await Promise.allSettled([
          apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos'),
          apiClient.get<AnalyticsDashboard>('/api/v1/analytics/dashboard'),
        ]);

        if (repoData.status === 'fulfilled') {
          setRepos(repoData.value.repositories || []);
        }
        if (analyticsData.status === 'fulfilled') {
          setAnalytics(analyticsData.value);
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const indexedCount = repos.filter(r => r.indexed_status === true).length;

  const stats = [
    {
      title: "Repositories",
      value: loading ? "—" : repos.length,
      icon: GitBranch,
      trend: indexedCount > 0 ? { value: `${indexedCount} indexed`, positive: true } : undefined,
    },
    {
      title: "AI Queries",
      value: loading ? "—" : (analytics?.total_queries ?? "—"),
      icon: MessageSquare,
      subtitle: analytics ? `${(analytics.total_tokens / 1000).toFixed(1)}k tokens used` : "Chat with indexed repos",
    },
    {
      title: "PRs Analyzed",
      value: "—",
      icon: GitPullRequest,
      subtitle: "Review pull requests",
    },
    {
      title: "System Status",
      value: "Operational",
      icon: Activity,
    },
  ];

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
        {/* Repositories overview */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold text-card-foreground">Your Repositories</h2>
          <div className="mt-4 space-y-3">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : repos.length === 0 ? (
              <div className="text-center py-8">
                <GitBranch className="h-8 w-8 mx-auto text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">No repositories connected yet</p>
                <Link to="/repositories">
                  <Button size="sm" className="mt-3 gap-2">
                    <Plus className="h-3 w-3" />
                    Connect Repository
                  </Button>
                </Link>
              </div>
            ) : (
              repos.slice(0, 5).map((repo) => (
                <div key={repo.id} className="flex items-start gap-3 rounded-lg p-2 hover:bg-accent transition-colors">
                  <span className="text-base">📦</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-card-foreground font-medium truncate">{repo.full_name}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {repo.language ? `${repo.language} · ` : ''}
                      {repo.indexed_status ? 'Indexed' : (repo.indexing_progress > 0 ? 'Indexing...' : 'Not indexed')}
                    </p>
                  </div>
                  {repo.indexed_status && (
                    <span className="shrink-0 text-[10px] rounded-full bg-green-500/10 text-green-500 px-2 py-0.5">
                      Ready
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
          {repos.length > 5 && (
            <Link to="/repositories" className="mt-3 block text-xs text-primary hover:underline">
              View all {repos.length} repositories →
            </Link>
          )}
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

          {/* Usage summary */}
          {analytics && analytics.total_queries > 0 && (
            <div className="mt-5 pt-4 border-t border-border">
              <p className="text-xs font-medium text-muted-foreground mb-3">Usage Summary</p>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Total Queries</span>
                  <span className="font-medium text-foreground">{analytics.total_queries.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Tokens Used</span>
                  <span className="font-medium text-foreground">{(analytics.total_tokens / 1000).toFixed(1)}k</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Repos Indexed</span>
                  <span className="font-medium text-foreground">{analytics.total_repos_indexed}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
