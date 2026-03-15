import { useState, useEffect } from "react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  GitPullRequest, Plus, Minus, ChevronRight, Check, MessageSquare,
  Loader2, AlertCircle, ShieldAlert, Zap, Search, LayoutList, RefreshCw,
  ExternalLink
} from "lucide-react";
import { useRepositories } from "@/hooks/useRepositories";
import { usePullRequests } from "@/hooks/usePullRequests";
import type { PullRequest, PRReviewResponse } from "@/lib/api";

const prStatusVariant = (s: string) =>
  s === "open" ? "primary" : s === "merged" ? "success" : "default";

export default function PullRequestsPage() {
  const { repos, loading: reposLoading } = useRepositories();
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const { pulls, loading: pullsLoading, error, fetchPulls, performReview, reviewing, reviewError } = usePullRequests(selectedRepoId || undefined);

  const [selectedPr, setSelectedPr] = useState<PullRequest | null>(null);
  const [reviewResults, setReviewResults] = useState<Record<number, PRReviewResponse>>({});

  useEffect(() => {
    if (repos.length > 0 && !selectedRepoId) {
      setSelectedRepoId(repos[0].id);
    }
  }, [repos, selectedRepoId]);

  useEffect(() => {
    if (selectedRepoId) {
      fetchPulls(selectedRepoId);
    }
  }, [selectedRepoId, fetchPulls]);

  const handleReview = async (pr: PullRequest) => {
    try {
      const result = await performReview(pr);
      setReviewResults(prev => ({ ...prev, [pr.number]: result }));
    } catch (err) {
      // Error handled by hook
    }
  };

  const currentReview = selectedPr ? reviewResults[selectedPr.number] : null;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Pull Requests</h1>
          <p className="mt-1 text-sm text-muted-foreground/80">AI-powered code reviews for your connected repositories</p>
        </div>

        {/* Repo Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Repo:</span>
          {reposLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
            <select
              value={selectedRepoId || ""}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="h-9 rounded-md border border-input bg-card px-3 py-1 text-sm outline-none focus:ring-1 focus:ring-primary"
            >
              {repos.map(r => (
                <option key={r.id} value={r.id}>{r.repo_name}</option>
              ))}
              {repos.length === 0 && <option value="">No repos connected</option>}
            </select>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* PR List */}
        <div className="lg:col-span-2 space-y-2">
          {pullsLoading ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mb-2" />
              <p className="text-sm">Fetching pull requests...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-20 text-center border rounded-xl bg-card border-dashed">
              <AlertCircle className="h-8 w-8 text-destructive mb-2" />
              <p className="text-sm text-muted-foreground px-4">{error}</p>
            </div>
          ) : pulls.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center border rounded-xl bg-card border-dashed">
              <LayoutList className="h-8 w-8 text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">No open pull requests found</p>
            </div>
          ) : (
            pulls.map((pr) => (
              <button
                key={pr.number}
                onClick={() => setSelectedPr(pr)}
                className={`w-full rounded-xl border p-4 text-left transition-all duration-300 relative overflow-hidden group ${selectedPr?.number === pr.number
                  ? "border-primary bg-primary/10 shadow-[0_0_15px_-3px_hsl(var(--primary)/0.2)]"
                  : "border-border/50 bg-card/40 hover:border-primary/40 hover:bg-card/60 hover:-translate-y-0.5"
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    <GitPullRequest className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-card-foreground leading-tight">{pr.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        #{pr.number} by {pr.author} · {new Date(pr.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
                <div className="mt-2 flex items-center gap-3">
                  <StatusBadge status={pr.state} variant={prStatusVariant(pr.state)} />
                  <span className="flex items-center gap-1 text-xs text-success"><Plus className="h-3 w-3" />{pr.additions}</span>
                  <span className="flex items-center gap-1 text-xs text-destructive"><Minus className="h-3 w-3" />{pr.deletions}</span>
                </div>
              </button>
            ))
          )}
        </div>

        {/* PR Detail */}
        <div className="lg:col-span-3">
          {selectedPr ? (
            <div className="glass-card rounded-xl p-6 space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-card-foreground leading-tight">{selectedPr.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    #{selectedPr.number} • by {selectedPr.author} • {new Date(selectedPr.created_at).toLocaleString()}
                  </p>
                </div>
                <a
                  href={selectedPr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 transition-colors text-xs font-medium"
                  title="Open PR on GitHub"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  View on GitHub
                </a>
              </div>

              {/* Diff preview */}
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Change Overview</p>
                <div className="flex gap-4 text-sm">
                  <div className="flex flex-col">
                    <span className="text-lg font-semibold text-success">+{selectedPr.additions}</span>
                    <span className="text-xs text-muted-foreground">Additions</span>
                  </div>
                  <div className="h-10 w-px bg-border mx-2" />
                  <div className="flex flex-col">
                    <span className="text-lg font-semibold text-destructive">-{selectedPr.deletions}</span>
                    <span className="text-xs text-muted-foreground">Deletions</span>
                  </div>
                </div>
              </div>

              {/* AI Review Action */}
              {!currentReview && (
                <div className="flex flex-col items-center justify-center p-8 border rounded-lg border-dashed bg-accent/5">
                  <Zap className="h-8 w-8 text-primary mb-3" />
                  <h3 className="font-medium mb-1">AI Code Review</h3>
                  <p className="text-sm text-muted-foreground text-center mb-4">
                    Get an instant AI-powered review of this pull request's logic, security, and performance.
                  </p>
                  <Button
                    onClick={() => handleReview(selectedPr)}
                    disabled={reviewing !== null}
                    className="gap-2"
                  >
                    {reviewing === selectedPr.number ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Zap className="h-4 w-4" />
                    )}
                    {reviewing === selectedPr.number ? "Analyzing Code..." : "Start AI Review"}
                  </Button>
                </div>
              )}

              {/* AI Review Results */}
              {currentReview && (
                <div className="space-y-6 animate-in fade-in duration-500">
                  <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-4 w-4 text-primary" />
                      <p className="text-xs font-bold text-primary uppercase tracking-wider">AI Assessment</p>
                    </div>
                    <p className="text-sm text-card-foreground leading-relaxed">{currentReview.summary}</p>
                  </div>

                  {/* Structured Feedback Grid */}
                  <div className="grid gap-4 sm:grid-cols-2">
                    {/* Issues */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-destructive">
                        <AlertCircle className="h-4 w-4" />
                        <h4 className="text-sm font-semibold">Potential Issues</h4>
                      </div>
                      <ul className="space-y-2">
                        {currentReview.potential_issues.length > 0 ? (
                          currentReview.potential_issues.map((msg, i) => (
                            <li key={i} className="text-sm text-muted-foreground pl-3 border-l-2 border-destructive/30">
                              {msg}
                            </li>
                          ))
                        ) : (
                          <li className="text-sm text-muted-foreground italic">No logical issues detected.</li>
                        )}
                      </ul>
                    </div>

                    {/* Suggestions */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-primary">
                        <MessageSquare className="h-4 w-4" />
                        <h4 className="text-sm font-semibold">Refactoring</h4>
                      </div>
                      <ul className="space-y-2">
                        {currentReview.refactoring_suggestions.map((msg, i) => (
                          <li key={i} className="text-sm text-muted-foreground pl-3 border-l-2 border-primary/30">
                            {msg}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Security */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-warning">
                        <ShieldAlert className="h-4 w-4" />
                        <h4 className="text-sm font-semibold">Security</h4>
                      </div>
                      <ul className="space-y-2">
                        {currentReview.security_warnings.length > 0 ? (
                          currentReview.security_warnings.map((msg, i) => (
                            <li key={i} className="text-sm text-muted-foreground pl-3 border-l-2 border-warning/30">
                              {msg}
                            </li>
                          ))
                        ) : (
                          <li className="text-sm text-muted-foreground italic">No security concerns found.</li>
                        )}
                      </ul>
                    </div>

                    {/* Performance */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-success">
                        <Zap className="h-4 w-4" />
                        <h4 className="text-sm font-semibold">Performance</h4>
                      </div>
                      <ul className="space-y-2">
                        {currentReview.performance_notes.map((msg, i) => (
                          <li key={i} className="text-sm text-muted-foreground pl-3 border-l-2 border-success/30">
                            {msg}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {reviewError && (
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-destructive/5 border border-destructive/20 text-destructive text-sm">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <p>{reviewError}</p>
                    </div>
                  )}

                  <div className="flex gap-3 pt-4 border-t border-border">
                    <Button
                      className="gap-2"
                      variant="outline"
                      onClick={() => window.open(selectedPr.url, '_blank', 'noopener,noreferrer')}
                    >
                      <Check className="h-4 w-4" /> Approve on GitHub
                    </Button>
                    <Button
                      variant="ghost"
                      className="text-muted-foreground hover:text-foreground gap-2"
                      onClick={() => handleReview(selectedPr)}
                      disabled={reviewing !== null}
                    >
                      {reviewing === selectedPr.number ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      Re-run Analysis
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] rounded-xl border border-dashed border-border/50 bg-card/10 glass-panel animate-pulse-slow">
              <GitPullRequest className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <p className="text-sm text-muted-foreground">Select a pull request to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


