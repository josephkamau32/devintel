import { useOutletContext } from 'react-router-dom';
import { useHealthScore, useRefreshHealth, useAutoFix } from '../../hooks/useAPI';
import type { Repository } from '../../types/repository';
import { Activity, RefreshCw, Loader2, Shield, Gauge, Code2, BookOpen, TestTube, Wrench, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import { useState } from 'react';
import toast from 'react-hot-toast';

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

const dimensionMeta = [
  { key: 'security' as const, label: 'Security', icon: Shield, desc: 'Vulnerability patterns, secret exposure, input validation' },
  { key: 'maintainability' as const, label: 'Maintainability', icon: Gauge, desc: 'Code structure, coupling, cohesion' },
  { key: 'complexity' as const, label: 'Complexity', icon: Code2, desc: 'Cyclomatic complexity, nesting depth' },
  { key: 'documentation' as const, label: 'Documentation', icon: BookOpen, desc: 'Docstrings, comments, README quality' },
  { key: 'test_coverage' as const, label: 'Test Coverage', icon: TestTube, desc: 'Test file presence, assertion patterns' },
];

export function HealthTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data: health, isLoading, isError } = useHealthScore(repository.id);
  const refreshHealth = useRefreshHealth();
  const autoFix = useAutoFix();
  const [fixingIssue, setFixingIssue] = useState<string | null>(null);

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  const handleRefresh = () => {
    refreshHealth.mutate(repository.id, {
      onSuccess: () => toast.success('Health analysis queued. Results will update shortly.'),
      onError: () => toast.error('Failed to queue health analysis.'),
    });
  };

  const handleAutoFix = async (issue: string) => {
    setFixingIssue(issue);
    autoFix.mutate(
      { repositoryId: repository.id, issueDescription: issue },
      {
        onSuccess: (data) => {
          if (data.pr_url) {
            toast.success(`Fix PR created! ${data.pr_url}`);
          } else {
            toast.success(data.message || 'Auto-fix generated.');
          }
          setFixingIssue(null);
        },
        onError: () => {
          toast.error('Auto-fix failed. Please try again.');
          setFixingIssue(null);
        },
      },
    );
  };

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <Activity className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Index required</h2>
        <p className="text-body text-text-tertiary">Index this repository to run health analysis.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 text-brand-400 animate-spin-slow" />
      </div>
    );
  }

  if (isError || !health) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <Activity className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">No health data yet</h2>
        <p className="text-body text-text-tertiary mb-6">Run a health analysis to see detailed scores.</p>
        <button onClick={handleRefresh} disabled={refreshHealth.isPending} className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
          {refreshHealth.isPending ? <Loader2 className="h-4 w-4 animate-spin-slow" /> : <RefreshCw className="h-4 w-4" />}
          Run Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-h3 text-text-primary">Code Health Report</h2>
          {health.computed_at && (
            <p className="text-xs text-text-quaternary mt-1">Last computed {new Date(health.computed_at).toLocaleString()}</p>
          )}
        </div>
        <button onClick={handleRefresh} disabled={refreshHealth.isPending} className="action-pill">
          {refreshHealth.isPending ? <Loader2 className="h-3 w-3 animate-spin-slow" /> : <RefreshCw className="h-3 w-3" />}
          Refresh
        </button>
      </div>

      {/* Dimension cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {dimensionMeta.map((dim) => {
          const Icon = dim.icon;
          const score = health.dimensions[dim.key];
          return (
            <div key={dim.key} className={clsx('card p-5', getScoreBg(score))}>
              <div className="flex items-center gap-3 mb-3">
                <div className={clsx('flex items-center justify-center w-9 h-9 rounded-lg', getScoreBg(score))}>
                  <Icon className={clsx('h-[18px] w-[18px]', getScoreColor(score))} />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-text-primary">{dim.label}</h4>
                  <p className="text-[10px] text-text-quaternary">{dim.desc}</p>
                </div>
              </div>
              <div className="flex items-end gap-3">
                <span className={clsx('text-stat font-bold', getScoreColor(score))}>
                  {Math.round(score)}
                </span>
                <div className="flex-1 score-bar-track">
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
            </div>
          );
        })}
      </div>

      {/* Issues with auto-fix */}
      {health.top_issues && health.top_issues.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
            <AlertTriangle className="h-4 w-4 text-status-warning" />
            <h3 className="text-sm font-semibold text-text-primary">Issues</h3>
          </div>
          <div className="divide-y divide-border">
            {health.top_issues.map((issue, i) => (
              <div key={i} className="flex items-start gap-3 px-5 py-3">
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-status-warning-muted text-status-warning text-[10px] font-bold mt-0.5">
                  {i + 1}
                </span>
                <p className="flex-1 text-sm text-text-secondary leading-relaxed">{issue}</p>
                <button
                  onClick={() => handleAutoFix(issue)}
                  disabled={fixingIssue === issue}
                  className="action-pill flex-shrink-0"
                >
                  {fixingIssue === issue ? (
                    <Loader2 className="h-3 w-3 animate-spin-slow" />
                  ) : (
                    <Wrench className="h-3 w-3" />
                  )}
                  Auto-fix
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
