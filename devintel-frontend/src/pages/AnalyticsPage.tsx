import { useAnalytics } from '../hooks/useAPI';
import { BarChart3, Loader2, MessageSquareText, Coins, Database, Clock } from 'lucide-react';
import type { UsageTrend, RepoUsage } from '../types/api';

function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

function TrendChart({ data }: { data: UsageTrend[] }) {
  if (data.length === 0) return null;
  const max = Math.max(...data.map((d) => d.queries), 1);

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-border">
        <h3 className="text-sm font-semibold text-text-primary">Query Usage Over Time</h3>
      </div>
      <div className="p-5">
        <div className="flex items-end gap-1.5 h-40">
          {data.map((d, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
              <span className="text-[9px] text-text-quaternary opacity-0 group-hover:opacity-100 transition-opacity">
                {d.queries}
              </span>
              <div
                className="w-full rounded-t bg-brand-500/70 hover:bg-brand-500 transition-all duration-300 min-h-[2px]"
                style={{ height: `${(d.queries / max) * 100}%` }}
              />
              <span className="text-[8px] text-text-quaternary -rotate-45 origin-top-left mt-1 hidden sm:block">
                {d.date.slice(5)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TopRepos({ data }: { data: RepoUsage[] }) {
  if (data.length === 0) return null;
  const max = Math.max(...data.map((d) => d.queries), 1);

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-border">
        <h3 className="text-sm font-semibold text-text-primary">Most Queried Repositories</h3>
      </div>
      <div className="p-5 space-y-3">
        {data.map((repo, i) => (
          <div key={i} className="animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-text-primary truncate">{repo.repo_name}</span>
              <span className="text-xs text-text-quaternary">{repo.queries}</span>
            </div>
            <div className="score-bar-track">
              <div
                className="score-bar-fill bg-brand-500"
                style={{ width: `${(repo.queries / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalyticsPage() {
  const { data, isLoading } = useAnalytics();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 text-brand-400 animate-spin-slow" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <BarChart3 className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">No analytics data</h2>
        <p className="text-body text-text-tertiary">Start using DevIntel to see your analytics here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-h2 text-text-primary mb-1">Analytics</h1>
        <p className="text-body text-text-tertiary">Your DevIntel usage and insights.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-1">
            <MessageSquareText className="h-4 w-4 text-text-quaternary" />
            <span className="text-xs font-medium text-text-quaternary uppercase tracking-wider">Queries</span>
          </div>
          <div className="text-stat-sm font-bold text-text-primary">{data.total_queries.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-1">
            <Coins className="h-4 w-4 text-text-quaternary" />
            <span className="text-xs font-medium text-text-quaternary uppercase tracking-wider">Tokens</span>
          </div>
          <div className="text-stat-sm font-bold text-text-primary">{formatCompact(data.total_tokens)}</div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-1">
            <Database className="h-4 w-4 text-text-quaternary" />
            <span className="text-xs font-medium text-text-quaternary uppercase tracking-wider">Indexed</span>
          </div>
          <div className="text-stat-sm font-bold text-text-primary">{data.total_repos_indexed}</div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-text-quaternary" />
            <span className="text-xs font-medium text-text-quaternary uppercase tracking-wider">Last Active</span>
          </div>
          <div className="text-sm font-medium text-text-primary mt-1">
            {data.last_active_at ? new Date(data.last_active_at).toLocaleDateString() : '—'}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-4">
        <TrendChart data={data.usage_trend} />
        <TopRepos data={data.top_repositories} />
      </div>
    </div>
  );
}
