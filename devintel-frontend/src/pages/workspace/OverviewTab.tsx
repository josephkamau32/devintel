import { useOutletContext } from 'react-router-dom';
import { useHealthScore } from '../../hooks/useAPI';
import type { Repository } from '../../types/repository';
import { Activity, Shield, Gauge, BookOpen, TestTube, Code2, Sparkles, AlertTriangle, Lightbulb, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-score-excellent';
  if (score >= 70) return 'text-score-good';
  if (score >= 40) return 'text-score-warning';
  return 'text-score-critical';
}

function getScoreBg(score: number): string {
  if (score >= 90) return 'bg-score-excellent-muted';
  if (score >= 70) return 'bg-score-good-muted';
  if (score >= 40) return 'bg-score-warning-muted';
  return 'bg-score-critical-muted';
}

const dimensionIcons = {
  security: Shield,
  maintainability: Gauge,
  complexity: Code2,
  documentation: BookOpen,
  test_coverage: TestTube,
};

const dimensionLabels = {
  security: 'Security',
  maintainability: 'Maintainability',
  complexity: 'Complexity',
  documentation: 'Documentation',
  test_coverage: 'Test Coverage',
};

export function OverviewTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data: health, isLoading, isError } = useHealthScore(repository.id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 text-brand-400 animate-spin-slow" />
      </div>
    );
  }

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <Activity className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Repository not yet indexed</h2>
        <p className="text-body text-text-tertiary max-w-md mx-auto">
          Index this repository first to generate health reports, architecture analysis, and AI insights.
        </p>
      </div>
    );
  }

  if (isError || !health) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <Sparkles className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Analysis in progress</h2>
        <p className="text-body text-text-tertiary max-w-md mx-auto">
          Health analysis is being computed. This usually takes a few minutes after indexing completes.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* AI Executive Summary */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-brand-400" />
          <h2 className="text-sm font-semibold text-text-primary">AI Executive Summary</h2>
        </div>
        <div className="text-body text-text-secondary leading-relaxed whitespace-pre-line">
          {health.summary || 'No summary available yet.'}
        </div>
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border text-xs text-text-quaternary">
          <span>{health.files_analyzed} files analyzed</span>
          <span>·</span>
          <span>{health.language_detected || 'Unknown language'}</span>
          {health.computed_at && (
            <>
              <span>·</span>
              <span>Analyzed {new Date(health.computed_at).toLocaleDateString()}</span>
            </>
          )}
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Overall */}
        <div className={clsx('card p-4 flex flex-col items-center gap-2', getScoreBg(health.overall_score))}>
          <span className="text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">Overall</span>
          <span className={clsx('text-stat font-bold', getScoreColor(health.overall_score))}>
            {Math.round(health.overall_score)}
          </span>
        </div>
        {/* Dimensions */}
        {(Object.keys(dimensionLabels) as (keyof typeof dimensionLabels)[]).map((dim) => {
          const Icon = dimensionIcons[dim];
          const score = health.dimensions[dim];
          return (
            <div key={dim} className="card p-4 flex flex-col items-center gap-2">
              <div className="flex items-center gap-1">
                <Icon className="h-3 w-3 text-text-quaternary" />
                <span className="text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
                  {dimensionLabels[dim].split(' ')[0]}
                </span>
              </div>
              <span className={clsx('text-stat-sm font-bold', getScoreColor(score))}>
                {Math.round(score)}
              </span>
              <div className="w-full score-bar-track">
                <div
                  className={clsx('score-bar-fill', {
                    'bg-score-excellent': score >= 90,
                    'bg-score-good': score >= 70 && score < 90,
                    'bg-score-warning': score >= 40 && score < 70,
                    'bg-score-critical': score < 40,
                  })}
                  style={{ width: `${score}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Issues & Recommendations */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Top Issues */}
        <div className="card">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
            <AlertTriangle className="h-4 w-4 text-status-warning" />
            <h3 className="text-sm font-semibold text-text-primary">Top Issues</h3>
            <span className="ml-auto text-xs text-text-quaternary">{health.top_issues?.length || 0}</span>
          </div>
          <div className="p-4">
            {health.top_issues && health.top_issues.length > 0 ? (
              <ul className="space-y-3">
                {health.top_issues.map((issue, i) => (
                  <li key={i} className="flex gap-3 text-sm text-text-secondary animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-status-warning-muted text-status-warning text-[10px] font-bold mt-0.5">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{issue}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-text-quaternary">No issues found — looking good!</p>
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div className="card">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
            <Lightbulb className="h-4 w-4 text-brand-400" />
            <h3 className="text-sm font-semibold text-text-primary">Recommendations</h3>
            <span className="ml-auto text-xs text-text-quaternary">{health.recommendations?.length || 0}</span>
          </div>
          <div className="p-4">
            {health.recommendations && health.recommendations.length > 0 ? (
              <ul className="space-y-3">
                {health.recommendations.map((rec, i) => (
                  <li key={i} className="flex gap-3 text-sm text-text-secondary animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-brand-600/15 text-brand-400 text-[10px] font-bold mt-0.5">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{rec}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-text-quaternary">No recommendations at this time.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
