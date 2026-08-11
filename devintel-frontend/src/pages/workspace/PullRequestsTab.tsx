import { useOutletContext } from 'react-router-dom';
import { usePullRequests } from '../../hooks/useAPI';
import type { Repository } from '../../types/repository';
import { GitPullRequest, GitBranch, ExternalLink, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function PullRequestsTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data, isLoading } = usePullRequests(repository.id);

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <GitBranch className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Index required</h2>
        <p className="text-body text-text-tertiary">Index to view pull requests.</p>
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

  const pulls = data?.pulls || [];

  if (pulls.length === 0) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <GitPullRequest className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">No pull requests</h2>
        <p className="text-body text-text-tertiary">This repository has no recent pull requests.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden animate-fade-in">
      <div className="px-5 py-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Pull Requests</h3>
        <span className="text-xs text-text-quaternary">{pulls.length} PRs</span>
      </div>
      <div className="divide-y divide-border">
        {pulls.map((pr, i) => (
          <div
            key={pr.number}
            className="flex items-center gap-4 px-5 py-4 hover:bg-surface-3 transition-colors animate-slide-up"
            style={{ animationDelay: `${i * 30}ms` }}
          >
            <GitPullRequest
              className={clsx(
                'h-5 w-5 flex-shrink-0',
                pr.state === 'open' ? 'text-status-success' : pr.state === 'merged' ? 'text-brand-400' : 'text-text-quaternary',
              )}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary truncate">{pr.title}</span>
                <span className={clsx(
                  'flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded',
                  pr.state === 'open' ? 'bg-status-success-muted text-status-success' : pr.state === 'merged' ? 'bg-brand-600/15 text-brand-400' : 'bg-surface-4 text-text-quaternary',
                )}>
                  {pr.state}
                </span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-text-quaternary">
                <span>#{pr.number}</span>
                <span>by {pr.author}</span>
                <span>{formatDate(pr.created_at)}</span>
                <span className="text-status-success">+{pr.additions}</span>
                <span className="text-status-error">−{pr.deletions}</span>
              </div>
            </div>
            <a
              href={pr.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 flex items-center gap-1 text-xs text-text-tertiary hover:text-text-secondary transition-colors"
            >
              <ExternalLink className="h-3 w-3" />
              View
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
