import { useState, useEffect } from "react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { GitPullRequest, Plus, Minus, ChevronRight, Check, MessageSquare, Loader2, Github } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import type { Repository } from "@/lib/types";

interface GitHubPR {
  id: number;
  number: number;
  title: string;
  html_url: string;
  state: 'open' | 'closed';
  merged_at: string | null;
  created_at: string;
  additions: number;
  deletions: number;
  user: {
    login: string;
    avatar_url: string;
  };
  base: {
    repo: {
      full_name: string;
    };
  };
}

interface PRDisplay {
  id: string;
  title: string;
  author: string;
  authorAvatar: string;
  status: 'open' | 'merged' | 'closed';
  createdAt: string;
  repository: string;
  additions: number;
  deletions: number;
  number: number;
  html_url: string;
  aiSummary?: string;
  suggestedChanges?: string[];
}

const prStatusVariant = (s: string) =>
  s === "open" ? "primary" : s === "merged" ? "success" : "default";

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return 'just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function PullRequestsPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [pullRequests, setPullRequests] = useState<PRDisplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<PRDisplay | null>(null);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const repoData = await apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos');
        const repoList = repoData.repositories || [];
        setRepos(repoList);

        // Fetch PRs for each repo from GitHub
        const allPRs: PRDisplay[] = [];
        for (const repo of repoList) {
          try {
            const token = localStorage.getItem('access_token');
            // Use the GitHub API through our backend proxy or directly
            const prs = await apiClient.get<GitHubPR[]>(`/api/v1/repos/${repo.id}/pulls`) as unknown;
            // If backend doesn't have a PR listing endpoint, we handle gracefully
          } catch {
            // PR fetching not available for this repo — skip silently
          }
        }
        setPullRequests(allPRs);
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleAIReview = async (pr: PRDisplay) => {
    if (!pr || reviewing) return;
    setReviewing(true);
    try {
      const repo = repos.find(r => r.full_name === pr.repository || r.name === pr.repository);
      if (!repo) {
        toast.error('Repository not found');
        return;
      }
      const review = await apiClient.post<{
        summary: string;
        potential_issues: string[];
        refactoring_suggestions: string[];
        security_warnings: string[];
        performance_notes: string[];
      }>('/api/v1/pr-review', {
        repository_id: repo.id,
        pr_title: pr.title,
        pr_description: '',
        pull_request_diff: `PR #${pr.number}: ${pr.title}\n+${pr.additions} -${pr.deletions}`,
      });

      // Update the PR with AI review data
      const suggestedChanges = [
        ...review.potential_issues,
        ...review.refactoring_suggestions,
        ...review.security_warnings,
        ...review.performance_notes,
      ].filter(Boolean);

      const updatedPR = {
        ...pr,
        aiSummary: review.summary,
        suggestedChanges,
      };
      setPullRequests(prev => prev.map(p => p.id === pr.id ? updatedPR : p));
      setSelected(updatedPR);
      toast.success('AI review complete');
    } catch (err: any) {
      toast.error(err.message || 'AI review failed');
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Pull Requests</h1>
        <p className="mt-1 text-sm text-muted-foreground">AI-powered code reviews for your pull requests</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : pullRequests.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 rounded-xl border border-dashed border-border">
          <GitPullRequest className="h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">No pull requests yet</p>
          <p className="mt-1 text-xs text-muted-foreground max-w-sm text-center">
            {repos.length === 0
              ? 'Connect a repository first, then pull requests will appear here.'
              : 'Pull requests from your connected repositories will appear here once the PR review API is configured.'}
          </p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          {/* PR List */}
          <div className="lg:col-span-2 space-y-2">
            {pullRequests.map((pr) => (
              <button
                key={pr.id}
                onClick={() => setSelected(pr)}
                className={`w-full rounded-xl border p-4 text-left transition-colors ${selected?.id === pr.id
                    ? "border-primary bg-primary/5"
                    : "border-border bg-card hover:border-primary/30"
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    <GitPullRequest className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-card-foreground">{pr.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {pr.author} · {pr.repository} · {pr.createdAt}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
                <div className="mt-2 flex items-center gap-3">
                  <StatusBadge status={pr.status} variant={prStatusVariant(pr.status)} />
                  <span className="flex items-center gap-1 text-xs text-success"><Plus className="h-3 w-3" />{pr.additions}</span>
                  <span className="flex items-center gap-1 text-xs text-destructive"><Minus className="h-3 w-3" />{pr.deletions}</span>
                </div>
              </button>
            ))}
          </div>

          {/* PR Detail */}
          <div className="lg:col-span-3">
            {selected ? (
              <div className="rounded-xl border border-border bg-card p-6 space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-card-foreground">{selected.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    by {selected.author} · {selected.createdAt} · {selected.repository}
                  </p>
                </div>

                <div className="rounded-lg border border-border bg-muted p-4">
                  <p className="text-xs font-medium text-muted-foreground mb-2">Diff Summary</p>
                  <div className="flex gap-4 text-sm">
                    <span className="text-success">+{selected.additions} additions</span>
                    <span className="text-destructive">-{selected.deletions} deletions</span>
                  </div>
                </div>

                {selected.aiSummary && (
                  <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                    <p className="text-xs font-medium text-primary mb-2">AI Review Summary</p>
                    <p className="text-sm text-card-foreground leading-relaxed">{selected.aiSummary}</p>
                  </div>
                )}

                {selected.suggestedChanges && selected.suggestedChanges.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-card-foreground mb-3">Suggested Changes</p>
                    <ul className="space-y-2">
                      {selected.suggestedChanges.map((change, i) => (
                        <li key={i} className="flex items-start gap-2 rounded-lg border border-border bg-muted p-3 text-sm text-card-foreground">
                          <MessageSquare className="mt-0.5 h-4 w-4 text-primary shrink-0" />
                          {change}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <Button className="gap-2" onClick={() => handleAIReview(selected)} disabled={reviewing}>
                    {reviewing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                    {reviewing ? 'Reviewing...' : 'AI Review'}
                  </Button>
                  {selected.html_url && (
                    <Button variant="outline" onClick={() => window.open(selected.html_url, '_blank')}>
                      <Github className="h-4 w-4 mr-2" />View on GitHub
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-border">
                <p className="text-sm text-muted-foreground">Select a pull request to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
