import { useNavigate } from 'react-router-dom';
import { useRepositories } from '../hooks/useRepositories';
import { useAllHealthScores } from '../hooks/useAPI';
import { Sparkles, ArrowRight, AlertTriangle, Shield, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

export function InsightsPage() {
  const { repositories, isLoading } = useRepositories();
  const healthScores = useAllHealthScores(repositories);
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 text-brand-400 animate-spin-slow" />
      </div>
    );
  }

  const healthData = healthScores.data || {};
  const allIssues: { repo: string; repoId: string; issue: string }[] = [];
  const allRecs: { repo: string; repoId: string; rec: string }[] = [];

  Object.entries(healthData).forEach(([repoId, health]) => {
    health.top_issues?.forEach((issue) => {
      allIssues.push({ repo: health.repo_name, repoId, issue });
    });
    health.recommendations?.forEach((rec) => {
      allRecs.push({ repo: health.repo_name, repoId, rec });
    });
  });

  // Sort: repos with lower scores (more critical) first
  const sortedRepos = Object.entries(healthData)
    .sort(([, a], [, b]) => a.overall_score - b.overall_score);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-h2 text-text-primary mb-1">AI Insights</h1>
        <p className="text-body text-text-tertiary">
          Intelligence gathered across all your repositories.
        </p>
      </div>

      {repositories.length === 0 ? (
        <div className="card p-10 text-center">
          <Sparkles className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
          <h2 className="text-h3 text-text-primary mb-2">No insights yet</h2>
          <p className="text-body text-text-tertiary">Connect and index repositories to generate AI insights.</p>
        </div>
      ) : (
        <>
          {/* Critical issues across all repos */}
          {allIssues.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <AlertTriangle className="h-4 w-4 text-status-warning" />
                <h3 className="text-sm font-semibold text-text-primary">Issues Across Repositories</h3>
                <span className="ml-auto text-xs text-text-quaternary">{allIssues.length}</span>
              </div>
              <div className="divide-y divide-border">
                {allIssues.slice(0, 15).map((item, i) => (
                  <button
                    key={i}
                    onClick={() => navigate(`/repositories/${item.repoId}/health`)}
                    className="w-full flex items-start gap-3 px-5 py-3 text-left hover:bg-surface-3 transition-colors"
                  >
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-status-warning-muted text-status-warning text-[10px] font-bold mt-0.5">!</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-secondary">{item.issue}</p>
                      <p className="text-xs text-text-quaternary mt-0.5">{item.repo}</p>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-text-quaternary flex-shrink-0 mt-0.5" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {allRecs.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <Sparkles className="h-4 w-4 text-brand-400" />
                <h3 className="text-sm font-semibold text-text-primary">AI Recommendations</h3>
                <span className="ml-auto text-xs text-text-quaternary">{allRecs.length}</span>
              </div>
              <div className="divide-y divide-border">
                {allRecs.slice(0, 15).map((item, i) => (
                  <button
                    key={i}
                    onClick={() => navigate(`/repositories/${item.repoId}/health`)}
                    className="w-full flex items-start gap-3 px-5 py-3 text-left hover:bg-surface-3 transition-colors"
                  >
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-brand-600/15 text-brand-400 text-[10px] font-bold mt-0.5">✦</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-secondary">{item.rec}</p>
                      <p className="text-xs text-text-quaternary mt-0.5">{item.repo}</p>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-text-quaternary flex-shrink-0 mt-0.5" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Repo health ranking */}
          {sortedRepos.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <Shield className="h-4 w-4 text-text-tertiary" />
                <h3 className="text-sm font-semibold text-text-primary">Repository Health Ranking</h3>
              </div>
              <div className="divide-y divide-border">
                {sortedRepos.map(([repoId, health], i) => (
                  <button
                    key={repoId}
                    onClick={() => navigate(`/repositories/${repoId}`)}
                    className="w-full flex items-center gap-4 px-5 py-3 hover:bg-surface-3 transition-colors animate-slide-up"
                    style={{ animationDelay: `${i * 30}ms` }}
                  >
                    <span className="text-xs font-bold text-text-quaternary w-5">{i + 1}</span>
                    <span className={clsx(
                      'text-lg font-bold w-10 text-center',
                      health.overall_score >= 70 ? 'text-score-good' : health.overall_score >= 40 ? 'text-score-warning' : 'text-score-critical',
                    )}>
                      {Math.round(health.overall_score)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-text-primary truncate">{health.repo_name}</p>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-text-quaternary" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
