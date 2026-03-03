import { useAnalytics } from "@/hooks/useAnalytics";
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
import {
  Activity,
  RefreshCw,
  Cpu,
  Database,
  Clock,
  AlertCircle,
  FileCode,
  TrendingUp
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AnalyticsPage() {
  const { data, loading, error, refresh } = useAnalytics();

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
        <Activity className="h-10 w-10 text-primary animate-pulse" />
        <p className="text-sm text-muted-foreground animate-pulse">Calculating real-time metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <h2 className="text-lg font-semibold">Incomplete Data</h2>
        <p className="max-w-md text-sm text-muted-foreground">{error}</p>
        <Button onClick={refresh} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" /> Try Again
        </Button>
      </div>
    );
  }

  const hasTrendData = data && data.usage_trend.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" /> Usage Intelligence
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">Real-time performance and usage metrics for your RAG engine</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-full bg-success/10 px-3 py-1 text-[10px] font-bold text-success uppercase tracking-widest border border-success/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
            </span>
            Live
          </div>
          <Button variant="outline" size="sm" onClick={refresh} disabled={loading} className="gap-2">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-6 hover:border-primary/50 transition-colors shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-primary/10 p-2.5 text-primary">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Queries</p>
              <h3 className="text-2xl font-bold tabular-nums">{data?.total_queries || 0}</h3>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-6 hover:border-primary/50 transition-colors shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-warning/10 p-2.5 text-warning">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Token Usage</p>
              <h3 className="text-2xl font-bold tabular-nums">{(data?.total_tokens || 0).toLocaleString()}</h3>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-6 hover:border-primary/50 transition-colors shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-info/10 p-2.5 text-info">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Repos Indexed</p>
              <h3 className="text-2xl font-bold tabular-nums">{data?.total_repos_indexed || 0}</h3>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Usage Trend */}
        <div className="rounded-2xl border border-border bg-card flex flex-col shadow-sm">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-card-foreground">Query Velocity</h2>
              <p className="text-xs text-muted-foreground">Volume over last 7 active days</p>
            </div>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="p-5 h-72">
            {hasTrendData ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.usage_trend}>
                  <defs>
                    <linearGradient id="colorQueries" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border) / 0.3)" />
                  <XAxis
                    dataKey="date"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                    dy={10}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "12px",
                      fontSize: 12,
                      boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="queries"
                    stroke="hsl(var(--primary))"
                    fillOpacity={1}
                    fill="url(#colorQueries)"
                    strokeWidth={2.5}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center opacity-40">
                <Activity className="h-8 w-8 mb-2" />
                <p className="text-xs">No activity recorded in the last 7 days</p>
              </div>
            )}
          </div>
        </div>

        {/* Top Repositories */}
        <div className="rounded-2xl border border-border bg-card flex flex-col shadow-sm">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-card-foreground">Top Codebases</h2>
              <p className="text-xs text-muted-foreground">Engagement per repository</p>
            </div>
            <FileCode className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="p-5 flex-1 flex flex-col justify-center">
            {data && data.top_repositories.length > 0 ? (
              <div className="space-y-6">
                {data.top_repositories.map((repo, i) => {
                  const maxQueries = data.top_repositories[0].queries;
                  const percentage = (repo.queries / maxQueries) * 100;
                  return (
                    <div key={repo.repo_name}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-accent text-[10px] font-bold">
                            #{i + 1}
                          </div>
                          <p className="text-sm font-medium">{repo.repo_name}</p>
                        </div>
                        <span className="text-xs font-medium text-muted-foreground">{repo.queries} queries</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-1000 ease-out"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center opacity-40">
                <Database className="h-8 w-8 mb-2" />
                <p className="text-xs">No repository activity detected</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="text-center">
        <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold flex items-center justify-center gap-2">
          {data?.last_active_at ? (
            <>Last Engine Activity: {new Date(data.last_active_at).toLocaleString()}</>
          ) : (
            <>Engine Standby</>
          )}
        </p>
      </div>
    </div>
  );
}
