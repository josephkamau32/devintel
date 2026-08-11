import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle, RotateCw, ArrowRight, Activity } from 'lucide-react';
import { Repository } from '../types/repository';
import type { HealthReport } from '../types/api';
import { clsx } from 'clsx';

interface RepositoryCardProps {
  repository: Repository;
  onIndex: (id: string) => void;
  isTriggering?: boolean;
  healthReport?: HealthReport;
}

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-score-excellent';
  if (score >= 70) return 'text-score-good';
  if (score >= 40) return 'text-score-warning';
  return 'text-score-critical';
}

function getScoreBg(score: number): string {
  if (score >= 90) return 'bg-score-excellent-muted border-score-excellent/20';
  if (score >= 70) return 'bg-score-good-muted border-score-good/20';
  if (score >= 40) return 'bg-score-warning-muted border-score-warning/20';
  return 'bg-score-critical-muted border-score-critical/20';
}

function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 40) return 'Fair';
  return 'Needs work';
}

export const RepositoryCard: React.FC<RepositoryCardProps> = ({ repository, onIndex, isTriggering, healthReport }) => {
  const navigate = useNavigate();
  const isIndexing = ['pending', 'indexing', 'cloning', 'chunking', 'embedding'].includes(repository.indexing_status);
  const isCompleted = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
      case 'complete':
        return {
          icon: <CheckCircle2 className="w-3.5 h-3.5" />,
          color: 'text-status-success',
          bg: 'bg-status-success-muted',
          border: 'border-status-success/20',
          label: 'Indexed',
        };
      case 'failed':
        return {
          icon: <XCircle className="w-3.5 h-3.5" />,
          color: 'text-status-error',
          bg: 'bg-status-error-muted',
          border: 'border-status-error/20',
          label: 'Failed',
        };
      case 'pending':
      case 'indexing':
      case 'cloning':
      case 'chunking':
      case 'embedding':
        return {
          icon: <Loader2 className="w-3.5 h-3.5 animate-spin-slow" />,
          color: 'text-status-info',
          bg: 'bg-status-info-muted',
          border: 'border-status-info/20',
          label: status.charAt(0).toUpperCase() + status.slice(1),
        };
      default:
        return {
          icon: null,
          color: 'text-text-quaternary',
          bg: 'bg-surface-3',
          border: 'border-border',
          label: 'Not indexed',
        };
    }
  };

  const statusConfig = getStatusConfig(repository.indexing_status);

  return (
    <div className="group card-interactive p-5 flex flex-col">
      {/* Top: name + status */}
      <div className="flex justify-between items-start mb-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-text-primary truncate">{repository.repo_name}</h3>
          <p className="text-xs text-text-quaternary truncate mt-0.5">{repository.full_name}</p>
        </div>
        <div className={`flex-shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${statusConfig.color} ${statusConfig.bg} border ${statusConfig.border}`}>
          {statusConfig.icon}
          <span>{statusConfig.label}</span>
        </div>
      </div>

      {/* Intelligence section */}
      {healthReport ? (
        <>
          {/* Health score */}
          <div className="flex items-center gap-3 mb-3">
            <div className={clsx(
              'flex items-center justify-center w-11 h-11 rounded-lg text-lg font-bold border',
              getScoreBg(healthReport.overall_score),
              getScoreColor(healthReport.overall_score),
            )}>
              {Math.round(healthReport.overall_score)}
            </div>
            <div className="min-w-0 flex-1">
              <div className={clsx('text-xs font-semibold', getScoreColor(healthReport.overall_score))}>
                {getScoreLabel(healthReport.overall_score)} Health
              </div>
              <div className="text-[10px] text-text-quaternary mt-0.5">
                {healthReport.files_analyzed} files · {healthReport.language_detected || repository.language || 'Unknown'}
              </div>
            </div>
          </div>

          {/* Dimension bars */}
          <div className="grid grid-cols-5 gap-1.5 mb-3">
            {(['security', 'maintainability', 'complexity', 'documentation', 'test_coverage'] as const).map((dim) => {
              const score = healthReport.dimensions[dim];
              return (
                <div key={dim} className="flex flex-col items-center gap-1">
                  <span className="text-[9px] text-text-quaternary capitalize">{dim.slice(0, 4)}</span>
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

          {/* AI Summary */}
          {healthReport.summary && (
            <p className="text-xs text-text-tertiary line-clamp-2 mb-3 leading-relaxed">
              {healthReport.summary}
            </p>
          )}
        </>
      ) : isCompleted ? (
        <div className="flex items-center gap-2 mb-3 p-3 bg-surface-3 rounded-lg border border-border">
          <Activity className="h-4 w-4 text-text-quaternary flex-shrink-0" />
          <p className="text-xs text-text-tertiary">Health analysis will run automatically.</p>
        </div>
      ) : !isIndexing ? (
        <div className="flex-1 flex items-center justify-center py-4">
          <p className="text-xs text-text-quaternary text-center">
            {repository.description || 'Index this repository to generate intelligence.'}
          </p>
        </div>
      ) : null}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-auto pt-3 border-t border-border">
        {isCompleted && (
          <button
            onClick={() => navigate(`/repositories/${repository.id}`)}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-subtle"
          >
            Open Workspace
            <ArrowRight className="h-3 w-3" />
          </button>
        )}
        <button
          onClick={() => onIndex(repository.id)}
          disabled={isIndexing || isTriggering}
          className={clsx(
            'flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150',
            isCompleted ? 'bg-surface-3 text-text-secondary hover:bg-surface-4 border border-border' : 'flex-1 bg-brand-600 hover:bg-brand-500 text-white shadow-subtle',
            (isIndexing || isTriggering) && 'opacity-50 cursor-not-allowed',
          )}
        >
          {isIndexing || isTriggering ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin-slow" />
              <span>Indexing…</span>
            </>
          ) : (
            <>
              {isCompleted ? <RotateCw className="w-3 h-3" /> : <Activity className="w-3 h-3" />}
              <span>{isCompleted ? 'Re-index' : 'Index'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
