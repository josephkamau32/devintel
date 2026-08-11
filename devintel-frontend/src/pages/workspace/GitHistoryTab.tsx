import { useOutletContext } from 'react-router-dom';
import { useGitHistory } from '../../hooks/useAPI';
import type { Repository } from '../../types/repository';
import { History, GitCommit, Loader2 } from 'lucide-react';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function GitHistoryTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data: history, isLoading } = useGitHistory(repository.id);

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <History className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Index required</h2>
        <p className="text-body text-text-tertiary">Index to view commit history.</p>
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

  const commits = history || [];

  if (commits.length === 0) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <GitCommit className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">No history</h2>
        <p className="text-body text-text-tertiary">No commit history available.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden animate-fade-in">
      <div className="px-5 py-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Commit History</h3>
        <span className="text-xs text-text-quaternary">{commits.length} commits</span>
      </div>
      <div className="divide-y divide-border">
        {commits.map((commit, i) => (
          <div
            key={commit.sha}
            className="flex gap-4 px-5 py-3.5 hover:bg-surface-3 transition-colors animate-slide-up"
            style={{ animationDelay: `${i * 20}ms` }}
          >
            {/* Timeline dot */}
            <div className="flex flex-col items-center flex-shrink-0 pt-1">
              <div className="w-2 h-2 rounded-full bg-brand-500" />
              {i < commits.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary line-clamp-1">{commit.message}</p>
              <div className="flex items-center gap-3 mt-1 text-xs text-text-quaternary">
                <span className="font-medium">{commit.author_name}</span>
                <code className="bg-surface-4 px-1.5 py-0.5 rounded text-[10px] font-mono">{commit.sha.slice(0, 7)}</code>
                <span>{formatDate(commit.authored_date)}</span>
                {(commit.additions > 0 || commit.deletions > 0) && (
                  <span>
                    <span className="text-status-success">+{commit.additions}</span>{' '}
                    <span className="text-status-error">−{commit.deletions}</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
