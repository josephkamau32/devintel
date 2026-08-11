import { useNavigate } from 'react-router-dom';
import type { Repository } from '../../types/repository';
import type { HealthReport } from '../../types/api';
import { clsx } from 'clsx';
import { ArrowRight, Activity } from 'lucide-react';

interface RepoHealthGridProps {
  repositories: Repository[];
  healthData: Record<string, HealthReport>;
}

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

export function RepoHealthGrid({ repositories, healthData }: RepoHealthGridProps) {
  const navigate = useNavigate();

  if (repositories.length === 0) {
    return (
      <div className="card p-8 text-center">
        <Activity className="h-6 w-6 text-text-quaternary mx-auto mb-3" />
        <p className="text-sm text-text-tertiary">No repositories connected yet.</p>
        <p className="text-xs text-text-quaternary mt-1">Connect a repository to see health scores.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Repository Health</h3>
        <button
          onClick={() => navigate('/repositories')}
          className="text-xs text-text-tertiary hover:text-text-secondary transition-colors flex items-center gap-1"
        >
          View all <ArrowRight className="h-3 w-3" />
        </button>
      </div>
      <div className="divide-y divide-border">
        {repositories.slice(0, 8).map((repo, idx) => {
          const health = healthData[repo.id];
          const isIndexed = repo.indexing_status === 'completed' || repo.indexing_status === 'complete';
          return (
            <button
              key={repo.id}
              onClick={() => navigate(`/repositories/${repo.id}`)}
              className={clsx(
                'w-full flex items-center gap-4 px-5 py-3 text-left hover:bg-surface-3 transition-colors animate-slide-up',
              )}
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              {/* Score */}
              <div className={clsx(
                'flex items-center justify-center w-10 h-10 rounded-lg text-sm font-bold flex-shrink-0',
                health ? getScoreBg(health.overall_score) : 'bg-surface-4',
                health ? getScoreColor(health.overall_score) : 'text-text-quaternary',
              )}>
                {health ? Math.round(health.overall_score) : '—'}
              </div>

              {/* Repo info */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-text-primary truncate">{repo.repo_name}</div>
                <div className="text-xs text-text-quaternary truncate">
                  {health
                    ? `${health.files_analyzed} files · ${health.language_detected || repo.language || 'Unknown'}`
                    : isIndexed
                      ? 'Health analysis pending'
                      : 'Not yet indexed'}
                </div>
              </div>

              {/* Mini score bars */}
              {health && (
                <div className="hidden sm:flex items-center gap-3 flex-shrink-0">
                  {(['security', 'maintainability', 'complexity'] as const).map((dim) => (
                    <div key={dim} className="flex flex-col items-end gap-0.5 w-14">
                      <span className="text-[9px] text-text-quaternary capitalize">{dim.slice(0, 3)}</span>
                      <div className="score-bar-track w-full">
                        <div
                          className={clsx('score-bar-fill', {
                            'bg-score-excellent': health.dimensions[dim] >= 90,
                            'bg-score-good': health.dimensions[dim] >= 70 && health.dimensions[dim] < 90,
                            'bg-score-warning': health.dimensions[dim] >= 40 && health.dimensions[dim] < 70,
                            'bg-score-critical': health.dimensions[dim] < 40,
                          })}
                          style={{ width: `${health.dimensions[dim]}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <ArrowRight className="h-3.5 w-3.5 text-text-quaternary flex-shrink-0" />
            </button>
          );
        })}
      </div>
    </div>
  );
}
