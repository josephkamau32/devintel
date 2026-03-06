import { useState, useEffect } from "react";
import { GitBranch, MessageSquare, GitPullRequest, Activity, ArrowRight, Plus, Zap, Loader2, Shield } from "lucide-react";
import { StatCard } from "@/components/shared/StatCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type { Repository, AnalyticsDashboard, CodeHealthReport } from "@/lib/types";

export default function DashboardPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [codeHealth, setCodeHealth] = useState<CodeHealthReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [repoData, analyticsData] = await Promise.allSettled([
          apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos'),
          apiClient.get<AnalyticsDashboard>('/api/v1/analytics/dashboard'),
        ]);

        if (repoData.status === 'fulfilled') {
          const repoList = repoData.value.repositories || [];
          setRepos(repoList);
          // Fetch code health for first indexed repo
          const firstIndexed = repoList.find(r => r.indexed_status);
          if (firstIndexed) {
            try {
              const health = await apiClient.get<CodeHealthReport>(`/api/v1/repos/${firstIndexed.id}/health`);
              setCodeHealth(health);
            } catch {
              // Health not yet computed — ignore silently
            }
          }
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

      {/* 3-column grid: Repos (2/3) | Quick Actions (1/3) */}
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
            <Link to="/code-health">
              <Button variant="outline" className="w-full justify-between">
                <span className="flex items-center gap-2"><Shield className="h-4 w-4" /> View Code Health</span>
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
                {analytics.total_cost_usd != null && (
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Total Spend</span>
                    <span className="font-medium text-emerald-400">${analytics.total_cost_usd.toFixed(4)}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Code Health widget — full-width card */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <h2 className="font-semibold text-card-foreground">Code Health</h2>
          </div>
          <Link to="/code-health" className="flex items-center gap-1 text-xs text-primary hover:underline">
            View Details <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : !codeHealth ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <Shield className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">No health data yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              Index a repository to generate a Code Health score
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-8 flex-wrap">
            {/* Score ring (inline SVG) */}
            <div className="flex flex-col items-center gap-1 shrink-0">
              {(() => {
                const score = Math.round(codeHealth.overall_score);
                const radius = 30;
                const circ = 2 * Math.PI * radius;
                const dash = (score / 100) * circ;
                const strokeColor =
                  score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
                return (
                  <svg width="88" height="88" viewBox="0 0 88 88">
                    <circle cx="44" cy="44" r={radius} fill="none"
                      stroke="currentColor" className="text-border" strokeWidth="7" />
                    <circle cx="44" cy="44" r={radius} fill="none"
                      stroke={strokeColor} strokeWidth="7" strokeLinecap="round"
                      strokeDasharray={`${dash} ${circ}`}
                      transform="rotate(-90 44 44)" />
                    <text x="44" y="49" textAnchor="middle"
                      className="fill-foreground" fontSize="18" fontWeight="700">
                      {score}
                    </text>
                  </svg>
                );
              })()}
              <span className="text-xs text-muted-foreground">/ 100</span>
            </div>

            {/* Dimension bars */}
            <div className="flex-1 min-w-0 space-y-2">
              {(
                [
                  ['Complexity', codeHealth.dimensions.complexity],
                  ['Documentation', codeHealth.dimensions.documentation],
                  ['Maintainability', codeHealth.dimensions.maintainability],
                  ['Test Coverage', codeHealth.dimensions.test_coverage],
                  ['Security', codeHealth.dimensions.security],
                ] as [string, number][]
              ).map(([label, val]) => {
                const pct = Math.round(val);
                const barColor =
                  pct >= 75 ? 'bg-green-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500';
                return (
                  <div key={label} className="flex items-center gap-2">
                    <span className="w-28 shrink-0 text-xs text-muted-foreground truncate">
                      {label}
                    </span>
                    <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full rounded-full ${barColor} transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-7 shrink-0 text-right text-xs font-medium text-foreground">
                      {pct}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Summary text */}
            {codeHealth.summary && (
              <p className="w-full text-xs text-muted-foreground leading-relaxed border-t border-border pt-3 mt-1">
                {codeHealth.summary}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
