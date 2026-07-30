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
          icon: <CheckCircle2 className="w-4 h-4" />,
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/20',
          label: 'Indexed',
        };
      case 'failed':
        return {
          icon: <XCircle className="w-4 h-4" />,
          color: 'text-red-400',
          bg: 'bg-red-500/10',
          border: 'border-red-500/20',
          label: 'Failed',
        };
      case 'pending': 
      case 'indexing':
      case 'cloning': 
      case 'chunking': 
      case 'embedding': 
        return {
          icon: <Loader2 className="w-4 h-4 animate-spin" />,
          color: 'text-sky-400',
          bg: 'bg-sky-500/10',
          border: 'border-sky-500/20',
          label: status.charAt(0).toUpperCase() + status.slice(1),
        };
      default:
        return {
          icon: null,
          color: 'text-slate-400',
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/20',
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
    C: 'bg-slate-400',
    Ruby: 'bg-red-400',
    PHP: 'bg-indigo-400',
  };

  return (
    <div className="group relative rounded-xl border border-slate-800 bg-slate-900/50 p-5 transition-all duration-300 hover:border-slate-700 hover:bg-slate-900/80 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-slate-900/50">
      {/* Top: repo info + status badge */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-3 min-w-0">
          <div className="flex-shrink-0 bg-slate-800 p-2 rounded-lg border border-slate-700/50 group-hover:border-slate-600/50 transition-colors">
            <Github className="w-5 h-5 text-slate-300" />
          </div>
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-white truncate">{repository.repo_name}</h3>
            <p className="text-xs text-slate-500 truncate">{repository.full_name}</p>
          </div>
        </div>
        <div className={`flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.color} ${statusConfig.bg} border ${statusConfig.border}`}>
          {statusConfig.icon}
          <span>{statusConfig.label}</span>
        </div>
      </div>
      
      {/* Description */}
      {repository.description && (
        <p className="text-slate-400 text-sm mb-4 line-clamp-2 leading-relaxed">{repository.description}</p>
      )}

      {/* Bottom: language + stars + action */}
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-800/50">
        <div className="flex space-x-4 text-xs text-slate-500">
          <div className="flex items-center space-x-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${langColor[repository.language || ''] || 'bg-slate-500'}`} />
            <span>{repository.language || 'Unknown'}</span>
          </div>
          {repository.stars > 0 && (
            <div className="flex items-center space-x-1">
              <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              <span>{repository.stars.toLocaleString()}</span>
            </div>
          )}
        </div>
        
        <button
          onClick={() => onIndex(repository.id)}
          disabled={isIndexing || isTriggering}
          className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
            isIndexing || isTriggering
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-violet-600 hover:bg-violet-500 text-white shadow-sm hover:shadow-md hover:shadow-violet-500/20'
          }`}
        >
          {isIndexing || isTriggering ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Indexing…</span>
            </>
          ) : (
            <>
              {isCompleted ? <RotateCw className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              <span>{isCompleted ? 'Re-index' : 'Index'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
