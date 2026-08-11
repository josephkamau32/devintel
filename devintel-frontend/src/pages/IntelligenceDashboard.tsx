import { useRepositories } from '../hooks/useRepositories';
import { useAnalytics, useAllHealthScores } from '../hooks/useAPI';
import type { Repository } from '../types/repository';
import { EngHealthScore } from '../components/dashboard/EngHealthScore';
import { StatCard } from '../components/dashboard/StatCard';
import { RepoHealthGrid } from '../components/dashboard/RepoHealthGrid';
import { UsageTrendChart } from '../components/dashboard/UsageTrendChart';
import { ActivityTimeline } from '../components/dashboard/ActivityTimeline';
import {
  FolderGit2,
  AlertTriangle,
  MessageSquareText,
  Coins,
  Database,
  Sparkles,
} from 'lucide-react';

/** Skeleton for the entire dashboard */
function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="h-8 w-64 rounded skeleton" />
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="stat-card">
            <div className="h-3 w-16 rounded skeleton mb-2" />
            <div className="h-8 w-20 rounded skeleton" />
          </div>
        ))}
      </div>
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-6 lg:col-span-2 h-64 skeleton" />
        <div className="card p-6 h-64 skeleton" />
      </div>
    </div>
  );
}

export function IntelligenceDashboard() {
  const { repositories, isLoading: reposLoading } = useRepositories();
  const analytics = useAnalytics();
  const healthScores = useAllHealthScores(repositories);

  if (reposLoading) return <DashboardSkeleton />;

  // Compute aggregate health score
  const healthData = healthScores.data || {};
  const healthValues = Object.values(healthData);
  const avgHealth =
    healthValues.length > 0
      ? Math.round(healthValues.reduce((sum, h) => sum + h.overall_score, 0) / healthValues.length)
      : null;

  // Count repos needing attention (health < 60)
  const reposNeedingAttention = healthValues.filter((h) => h.overall_score < 60).length;

  // Count critical issues
  const criticalIssues = healthValues.reduce(
    (sum, h) => sum + (h.top_issues?.length || 0),
    0,
  );

  const analyticsData = analytics.data;
  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  })();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-h2 text-text-primary mb-1">{greeting}</h1>
        <p className="text-body text-text-tertiary">
          {repositories.length > 0
            ? 'Here\'s your engineering intelligence overview.'
            : 'Connect a repository to start generating intelligence.'}
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          label="Repositories"
          value={repositories.length}
          icon={<FolderGit2 className="h-4 w-4" />}
        />
        <StatCard
          label="Needs Attention"
          value={reposNeedingAttention}
          icon={<AlertTriangle className="h-4 w-4" />}
          variant={reposNeedingAttention > 0 ? 'warning' : 'default'}
        />
        <StatCard
          label="Critical Issues"
          value={criticalIssues}
          icon={<Sparkles className="h-4 w-4" />}
          variant={criticalIssues > 0 ? 'error' : 'default'}
        />
        <StatCard
          label="AI Queries"
          value={analyticsData?.total_queries ?? 0}
          icon={<MessageSquareText className="h-4 w-4" />}
        />
        <StatCard
          label="Token Usage"
          value={analyticsData?.total_tokens ?? 0}
          icon={<Coins className="h-4 w-4" />}
          format="compact"
        />
        <StatCard
          label="Repos Indexed"
          value={analyticsData?.total_repos_indexed ?? repositories.filter((r: Repository) => r.indexing_status === 'completed' || r.indexing_status === 'complete').length}
          icon={<Database className="h-4 w-4" />}
        />
      </div>

      {/* Main content grid */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Left: Health Score + Trends */}
        <div className="lg:col-span-2 space-y-4">
          {/* Health + Trend row */}
          <div className="grid sm:grid-cols-2 gap-4">
            <EngHealthScore score={avgHealth} repoCount={healthValues.length} />
            <UsageTrendChart data={analyticsData?.usage_trend ?? []} />
          </div>

          {/* Repository Health Grid */}
          <RepoHealthGrid
            repositories={repositories}
            healthData={healthData}
          />
        </div>

        {/* Right: Activity Timeline */}
        <div>
          <ActivityTimeline
            analytics={analyticsData}
            repositories={repositories}
          />
        </div>
      </div>
    </div>
  );
}
