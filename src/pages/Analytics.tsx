import { mockAnalyticsData } from "@/lib/mock-data";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <p className="mt-1 text-sm text-muted-foreground">Usage insights and code intelligence trends</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Usage */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold text-card-foreground">AI Queries This Week</h2>
          <p className="mt-1 text-xs text-muted-foreground">Daily query volume</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockAnalyticsData.aiUsage}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 16%, 16%)" />
                <XAxis dataKey="date" tick={{ fill: "hsl(220, 10%, 55%)", fontSize: 12 }} />
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
                <Bar dataKey="queries" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Code Complexity */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold text-card-foreground">Code Complexity Trend</h2>
          <p className="mt-1 text-xs text-muted-foreground">Average complexity score over time</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockAnalyticsData.complexity}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 16%, 16%)" />
                <XAxis dataKey="date" tick={{ fill: "hsl(220, 10%, 55%)", fontSize: 12 }} />
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
                <Line type="monotone" dataKey="score" stroke="hsl(142, 71%, 45%)" strokeWidth={2} dot={{ fill: "hsl(142, 71%, 45%)", r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Files */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="font-semibold text-card-foreground">Most Queried Files</h2>
        <p className="mt-1 text-xs text-muted-foreground">Files your team asks about most</p>
        <div className="mt-4 space-y-3">
          {mockAnalyticsData.topFiles.map((file, i) => (
            <div key={file.file} className="flex items-center gap-4">
              <span className="w-4 text-xs text-muted-foreground">{i + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="truncate text-sm font-mono text-card-foreground">{file.file}</p>
                  <span className="shrink-0 text-xs text-muted-foreground">{file.queries} queries</span>
                </div>
                <div className="mt-1.5 h-1.5 w-full rounded-full bg-muted">
                  <div
                    className="h-1.5 rounded-full bg-primary transition-all"
                    style={{ width: `${(file.queries / 45) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
