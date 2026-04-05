import { useState, useEffect } from "react";
import { BarChart3, Loader2, MessageSquare, Coins, TrendingUp, DollarSign } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Repository, AnalyticsDashboard } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

// Shared recharts theme helpers
const gridColor = "hsl(222, 16%, 16%)";
const axisTickStyle = { fill: "hsl(220, 10%, 55%)", fontSize: 11 };
const tooltipStyle = {
  backgroundColor: "hsl(222, 16%, 9%)",
  border: "1px solid hsl(222, 16%, 16%)",
  borderRadius: "8px",
  color: "hsl(210, 20%, 95%)",
  fontSize: 12,
};

export default function AnalyticsPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [repoResult, analyticsResult] = await Promise.allSettled([
          apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos'),
          apiClient.get<AnalyticsDashboard>('/api/v1/analytics/dashboard'),
        ]);

        if (repoResult.status === 'fulfilled') {
          setRepos(repoResult.value.repositories || []);
        }
        if (analyticsResult.status === 'fulfilled') {
          setAnalytics(analyticsResult.value);
        }
      } catch (err) {
        console.error('Failed to fetch analytics data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Build language distribution chart from repo data
  const languageStats = repos.reduce((acc, repo) => {
    const lang = repo.language || 'Unknown';
    acc[lang] = (acc[lang] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const languageChartData = Object.entries(languageStats)
    .map(([language, count]) => ({ language, count }))
    .sort((a, b) => b.count - a.count);

  const indexedCount = repos.filter(r => r.indexed_status === true).length;
  const pendingCount = repos.filter(r => !r.indexed_status && r.indexing_progress > 0).length;
  const notIndexedCount = repos.length - indexedCount - pendingCount;

  const statusData = [
    { status: 'Indexed', count: indexedCount },
    { status: 'In Progress', count: pendingCount },
    { status: 'Not Indexed', count: notIndexedCount },
  ].filter(d => d.count > 0);

  // Format usage trend dates for display
  const usageTrendData = (analytics?.usage_trend || []).map(d => ({
    ...d,
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }));

  const monthlyCostData = (((analytics as unknown as Record<string, unknown>)?.monthly_cost as { date: string; cost_usd: number }[]) || []).map(
    (d: { date: string; cost_usd: number }) => ({
      date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      cost: d.cost_usd,
    })
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <p className="mt-1 text-sm text-muted-foreground">Usage insights and code intelligence trends</p>
      </div>

      {repos.length === 0 && !analytics ? (
        <div className="flex flex-col items-center justify-center py-16 rounded-xl border border-dashed border-border">
          <BarChart3 className="h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">No data yet</p>
          <p className="mt-1 text-xs text-muted-foreground">Connect and index repositories to see analytics</p>
        </div>
      ) : (
        <>
          {/* Top stat cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="h-4 w-4 text-primary" />
                <p className="text-sm text-muted-foreground">Total Queries</p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {analytics ? analytics.total_queries.toLocaleString() : repos.length}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 mb-2">
                <Coins className="h-4 w-4 text-amber-500" />
                <p className="text-sm text-muted-foreground">Tokens Used</p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {analytics ? `${(analytics.total_tokens / 1000).toFixed(1)}k` : '—'}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <p className="text-sm text-muted-foreground">Indexed Repos</p>
              </div>
              <p className="text-3xl font-bold text-green-500">{indexedCount}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-4 w-4 text-emerald-400" />
                <p className="text-sm text-muted-foreground">Total Spend</p>
              </div>
              <p className="text-3xl font-bold text-emerald-400">
                {analytics?.total_cost_usd != null
                  ? `$${analytics.total_cost_usd.toFixed(4)}`
                  : '—'}
              </p>
            </div>
          </div>

          {/* Charts row */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Queries Over Time */}
            {usageTrendData.length > 0 ? (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Queries Over Time</h2>
                <p className="mt-1 text-xs text-muted-foreground">Daily AI query activity (last 30 days)</p>
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={usageTrendData}>
                      <defs>
                        <linearGradient id="queryGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="date" tick={axisTickStyle} />
                      <YAxis tick={axisTickStyle} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Area
                        type="monotone"
                        dataKey="queries"
                        stroke="hsl(217, 91%, 60%)"
                        strokeWidth={2}
                        fill="url(#queryGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Queries Over Time</h2>
                <p className="mt-1 text-xs text-muted-foreground">Daily AI query activity</p>
                <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
                  No query data yet — start chatting with your repos!
                </div>
              </div>
            )}

            {/* Top Repositories by Usage */}
            {analytics && analytics.top_repositories.length > 0 ? (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Top Repositories</h2>
                <p className="mt-1 text-xs text-muted-foreground">Most queried repositories</p>
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics.top_repositories} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} horizontal={false} />
                      <XAxis type="number" tick={axisTickStyle} />
                      <YAxis
                        type="category"
                        dataKey="repo_name"
                        tick={axisTickStyle}
                        width={90}
                        tickFormatter={(v: string) => v.split('/').pop() || v}
                      />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="queries" fill="hsl(217, 91%, 60%)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : languageChartData.length > 0 ? (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Language Distribution</h2>
                <p className="mt-1 text-xs text-muted-foreground">Languages across your repositories</p>
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={languageChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="language" tick={axisTickStyle} />
                      <YAxis tick={axisTickStyle} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="count" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : null}
          </div>

          {/* Cost Over Time chart */}
          {monthlyCostData.length > 0 && (
            <div className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold text-card-foreground">Cost Over Time</h2>
              <p className="mt-1 text-xs text-muted-foreground">Daily AI spend — last 30 days (USD)</p>
              <div className="mt-4 h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={monthlyCostData}>
                    <defs>
                      <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis dataKey="date" tick={axisTickStyle} />
                    <YAxis tick={axisTickStyle} tickFormatter={(v: number) => `$${v.toFixed(4)}`} />
                    <Tooltip
                      contentStyle={tooltipStyle}
                      formatter={(v: number) => [`$${v.toFixed(5)}`, "Cost (USD)"]}
                    />
                    <Area
                      type="monotone"
                      dataKey="cost"
                      stroke="hsl(142, 71%, 45%)"
                      strokeWidth={2}
                      fill="url(#costGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Second charts row */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Language Distribution */}
            {languageChartData.length > 0 && analytics?.top_repositories.length > 0 && (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Language Distribution</h2>
                <p className="mt-1 text-xs text-muted-foreground">Languages across your repositories</p>
                <div className="mt-4 h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={languageChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="language" tick={axisTickStyle} />
                      <YAxis tick={axisTickStyle} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="count" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Indexing Status */}
            {statusData.length > 0 && (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Indexing Status</h2>
                <p className="mt-1 text-xs text-muted-foreground">Repository indexing progress</p>
                <div className="mt-4 h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={statusData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="status" tick={axisTickStyle} />
                      <YAxis tick={axisTickStyle} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="count" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          {/* Repository List */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold text-card-foreground">All Repositories</h2>
            <p className="mt-1 text-xs text-muted-foreground">Complete overview of your connected repos</p>
            <div className="mt-4 space-y-3">
              {repos.map((repo, i) => (
                <div key={repo.id} className="flex items-center gap-4">
                  <span className="w-4 text-xs text-muted-foreground">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="truncate text-sm font-mono text-card-foreground">{repo.full_name}</p>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {repo.indexed_status ? '✅ Indexed' : (repo.indexing_progress > 0 ? '⏳ Indexing' : '⬜ Not indexed')}
                      </span>
                    </div>
                    <div className="mt-1.5 h-1.5 w-full rounded-full bg-muted">
                      <div
                        className={`h-1.5 rounded-full transition-all ${repo.indexed_status ? 'bg-green-500' : (repo.indexing_progress > 0 ? 'bg-amber-500' : 'bg-muted-foreground/30')}`}
                        style={{ width: repo.indexed_status ? '100%' : (repo.indexing_progress > 0 ? `${repo.indexing_progress}%` : '0%') }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
