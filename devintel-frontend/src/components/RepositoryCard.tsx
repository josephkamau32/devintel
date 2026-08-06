import React from 'react';
import { Github, Play, Loader2, CheckCircle2, XCircle, RotateCw } from 'lucide-react';
import { Repository } from '../types/repository';

interface RepositoryCardProps {
  repository: Repository;
  onIndex: (id: string) => void;
  isTriggering?: boolean;
}

export const RepositoryCard: React.FC<RepositoryCardProps> = ({ repository, onIndex, isTriggering }) => {
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
  const isIndexing = ['pending', 'indexing', 'cloning', 'chunking', 'embedding'].includes(repository.indexing_status);
  const isCompleted = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  // Map common languages to colors
  const langColor: Record<string, string> = {
    Python: 'bg-blue-500',
    TypeScript: 'bg-blue-400',
    JavaScript: 'bg-yellow-400',
    Rust: 'bg-orange-500',
    Go: 'bg-cyan-400',
    Java: 'bg-red-500',
    'C++': 'bg-pink-500',
    C: 'bg-zinc-400',
    Ruby: 'bg-red-400',
    PHP: 'bg-indigo-400',
  };

  return (
    <div className="group card-interactive p-5">
      {/* Top: repo info + status badge */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-lg bg-surface-4 text-text-tertiary group-hover:text-text-secondary transition-colors">
            <Github className="w-[18px] h-[18px]" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-text-primary truncate">
              {repository.repo_name}
            </h3>
            <p className="text-xs text-text-quaternary truncate">
              {repository.full_name}
            </p>
          </div>
        </div>
        <div
          className={`flex-shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${statusConfig.color} ${statusConfig.bg} border ${statusConfig.border}`}
        >
          {statusConfig.icon}
          <span>{statusConfig.label}</span>
        </div>
      </div>
      
      {/* Description */}
      {repository.description && (
        <p className="text-body-sm text-text-tertiary mb-4 line-clamp-2">
          {repository.description}
        </p>
      )}

      {/* Bottom: language + stars + action */}
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-border">
        <div className="flex items-center gap-3.5 text-xs text-text-quaternary">
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${langColor[repository.language || ''] || 'bg-zinc-500'}`}
            />
            <span>{repository.language || 'Unknown'}</span>
          </div>
          {repository.stars > 0 && (
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              <span>{repository.stars.toLocaleString()}</span>
            </div>
          )}
        </div>
        
        <button
          onClick={() => onIndex(repository.id)}
          disabled={isIndexing || isTriggering}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 ${
            isIndexing || isTriggering
              ? 'bg-surface-4 text-text-quaternary cursor-not-allowed'
              : 'bg-brand-600 hover:bg-brand-500 text-white shadow-subtle'
          }`}
        >
          {isIndexing || isTriggering ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin-slow" />
              <span>Indexing…</span>
            </>
          ) : (
            <>
              {isCompleted ? <RotateCw className="w-3 h-3" /> : <Play className="w-3 h-3" />}
              <span>{isCompleted ? 'Re-index' : 'Index'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
