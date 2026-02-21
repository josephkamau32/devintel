import { useState, useEffect } from "react";
import { BarChart3, Loader2, GitBranch } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Repository } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function AnalyticsPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos');
        setRepos(data.repositories || []);
      } catch (err) {
        console.error('Failed to fetch analytics data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Build analytics from real repo data
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

      {repos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 rounded-xl border border-dashed border-border">
          <BarChart3 className="h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">No data yet</p>
          <p className="mt-1 text-xs text-muted-foreground">Connect and index repositories to see analytics</p>
        </div>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-card p-5">
              <p className="text-sm text-muted-foreground">Total Repositories</p>
              <p className="mt-1 text-3xl font-bold text-foreground">{repos.length}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <p className="text-sm text-muted-foreground">Indexed</p>
              <p className="mt-1 text-3xl font-bold text-success">{indexedCount}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="mt-1 text-3xl font-bold text-warning">{pendingCount + notIndexedCount}</p>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Language Distribution */}
            {languageChartData.length > 0 && (
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-semibold text-card-foreground">Language Distribution</h2>
                <p className="mt-1 text-xs text-muted-foreground">Languages across your repositories</p>
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={languageChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 16%, 16%)" />
                      <XAxis dataKey="language" tick={{ fill: "hsl(220, 10%, 55%)", fontSize: 12 }} />
                      <YAxis tick={{ fill: "hsl(220, 10%, 55%)", fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "hsl(222, 16%, 9%)",
                          border: "1px solid hsl(222, 16%, 16%)",
                          borderRadius: "8px",
                          color: "hsl(210, 20%, 95%)",
                          fontSize: 12,
                        }}
                      />
                      <Bar dataKey="count" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
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
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={statusData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 16%, 16%)" />
                      <XAxis dataKey="status" tick={{ fill: "hsl(220, 10%, 55%)", fontSize: 12 }} />
                      <YAxis tick={{ fill: "hsl(220, 10%, 55%)", fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "hsl(222, 16%, 9%)",
                          border: "1px solid hsl(222, 16%, 16%)",
                          borderRadius: "8px",
                          color: "hsl(210, 20%, 95%)",
                          fontSize: 12,
                        }}
                      />
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
                        className={`h-1.5 rounded-full transition-all ${repo.indexed_status ? 'bg-success' : (repo.indexing_progress > 0 ? 'bg-warning' : 'bg-muted-foreground/30')
                          }`}
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
