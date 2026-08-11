import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { usePullRequests, usePRReview } from '../../hooks/useAPI';
import type { Repository } from '../../types/repository';
import type { PRReviewResponse } from '../../types/api';
import { GitPullRequest, Loader2, AlertTriangle, Shield, Gauge, Wrench, Sparkles, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { clsx } from 'clsx';

export function ReviewsTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data: pullsData, isLoading } = usePullRequests(repository.id);
  const prReview = usePRReview();
  const [selectedPR, setSelectedPR] = useState<number | null>(null);
  const [review, setReview] = useState<PRReviewResponse | null>(null);

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  const handleReview = async (prNumber: number, prTitle: string) => {
    setSelectedPR(prNumber);
    setReview(null);
    try {
      const result = await prReview.mutateAsync({
        repositoryId: repository.id,
        prNumber,
        prTitle,
      });
      setReview(result);
    } catch {
      toast.error('Failed to generate PR review.');
    }
  };

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <GitPullRequest className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Index required</h2>
        <p className="text-body text-text-tertiary">Index this repository to review pull requests with AI.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* PR List */}
      <div className="card">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Pull Requests</h3>
        </div>
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-5 w-5 text-brand-400 animate-spin-slow mx-auto" />
          </div>
        ) : !pullsData?.pulls?.length ? (
          <div className="p-8 text-center">
            <GitPullRequest className="h-6 w-6 text-text-quaternary mx-auto mb-3" />
            <p className="text-sm text-text-tertiary">No open pull requests found.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {pullsData.pulls.map((pr) => (
              <div
                key={pr.number}
                className={clsx(
                  'flex items-center gap-4 px-5 py-3 hover:bg-surface-3 transition-colors',
                  selectedPR === pr.number && 'bg-surface-3',
                )}
              >
                <GitPullRequest className={clsx('h-4 w-4 flex-shrink-0', pr.state === 'open' ? 'text-status-success' : 'text-text-quaternary')} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary truncate">
                    #{pr.number} {pr.title}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-text-quaternary mt-0.5">
                    <span>{pr.author}</span>
                    <span>+{pr.additions} −{pr.deletions}</span>
                  </div>
                </div>
                <button
                  onClick={() => handleReview(pr.number, pr.title)}
                  disabled={prReview.isPending && selectedPR === pr.number}
                  className="action-pill flex-shrink-0"
                >
                  {prReview.isPending && selectedPR === pr.number ? (
                    <Loader2 className="h-3 w-3 animate-spin-slow" />
                  ) : (
                    <Sparkles className="h-3 w-3" />
                  )}
                  Review
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Results */}
      {review && (
        <div className="space-y-4 animate-slide-up">
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="h-4 w-4 text-status-success" />
              <h3 className="text-sm font-semibold text-text-primary">AI Review Summary</h3>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">{review.summary}</p>
          </div>

          {review.potential_issues.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <AlertTriangle className="h-4 w-4 text-status-warning" />
                <h4 className="text-sm font-semibold text-text-primary">Potential Issues</h4>
              </div>
              <ul className="p-4 space-y-2">
                {review.potential_issues.map((issue, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-status-warning flex-shrink-0">•</span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {review.security_warnings.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <Shield className="h-4 w-4 text-status-error" />
                <h4 className="text-sm font-semibold text-text-primary">Security Warnings</h4>
              </div>
              <ul className="p-4 space-y-2">
                {review.security_warnings.map((w, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-status-error flex-shrink-0">•</span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {review.refactoring_suggestions.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <Wrench className="h-4 w-4 text-brand-400" />
                <h4 className="text-sm font-semibold text-text-primary">Refactoring Suggestions</h4>
              </div>
              <ul className="p-4 space-y-2">
                {review.refactoring_suggestions.map((s, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-brand-400 flex-shrink-0">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {review.performance_notes.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <Gauge className="h-4 w-4 text-score-excellent" />
                <h4 className="text-sm font-semibold text-text-primary">Performance Notes</h4>
              </div>
              <ul className="p-4 space-y-2">
                {review.performance_notes.map((n, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-score-excellent flex-shrink-0">•</span>
                    {n}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
