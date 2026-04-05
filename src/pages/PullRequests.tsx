import { useState, useEffect } from "react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { DiffViewer } from "@/components/shared/DiffViewer";
import { Button } from "@/components/ui/button";
import {
  GitPullRequest, Plus, Minus, ChevronRight, Check,
  MessageSquare, Loader2, Github, ChevronDown, GitMerge, Code2
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import type { Repository } from "@/lib/types";

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

interface PullRequestResponse {
  id: number;
  number: number;
  title: string;
  html_url: string;
  state: 'open' | 'closed';
  merged_at: string | null;
  created_at: string;
  additions: number;
  deletions: number;
  user: { login: string; avatar_url: string };
  base: { repo: { full_name: string } };
}

interface PullRequestListResponse {
  pulls: PullRequestResponse[];
  repository_id: string;
}

type ActiveTab = 'overview' | 'diff';

const prStatusVariant = (s: string) =>
  s === "open" ? "primary" : s === "merged" ? "success" : "default";

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const diffMs = Date.now() - date.getTime();
  const diffHours = Math.floor(diffMs / 3_600_000);
  if (diffHours < 1) return 'just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

export default function PullRequestsPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [pullRequests, setPullRequests] = useState<PRDisplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingPRs, setLoadingPRs] = useState(false);
  const [selected, setSelected] = useState<PRDisplay | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const [stateFilter, setStateFilter] = useState<'open' | 'closed' | 'all'>('open');
  const [repoDropdownOpen, setRepoDropdownOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [diff, setDiff] = useState<string | null>(null);
  const [loadingDiff, setLoadingDiff] = useState(false);

  useEffect(() => {
    async function fetchRepos() {
      try {
        const repoData = await apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos');
        const repoList = repoData.repositories || [];
        setRepos(repoList);
        if (repoList.length > 0) setSelectedRepo(repoList[0]);
      } catch (err) {
        console.error('Failed to fetch repositories:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchRepos();
  }, []);

  useEffect(() => {
    if (!selectedRepo) return;
    fetchPRsForRepo(selectedRepo, stateFilter);
  }, [selectedRepo, stateFilter]);

  // Fetch diff when tab switches to diff
  useEffect(() => {
    if (activeTab === 'diff' && selected && selectedRepo && diff === null && !loadingDiff) {
      fetchDiff(selected, selectedRepo);
    }
  }, [activeTab, selected, selectedRepo, diff, loadingDiff]);

  const fetchPRsForRepo = async (repo: Repository, state: string) => {
    setLoadingPRs(true);
    setPullRequests([]);
    setSelected(null);
    setDiff(null);
    setActiveTab('overview');
    try {
      const data = await apiClient.get<PullRequestListResponse>(
        `/api/v1/repos/${repo.id}/pulls?state=${state}&per_page=30`
      );
      const prs: PRDisplay[] = (data.pulls || []).map((pr): PRDisplay => ({
        id: String(pr.id),
        title: pr.title,
        author: pr.user?.login || 'Unknown',
        authorAvatar: pr.user?.avatar_url || '',
        status: pr.merged_at ? 'merged' : pr.state,
        createdAt: timeAgo(pr.created_at),
        repository: pr.base?.repo?.full_name || repo.full_name,
        additions: pr.additions || 0,
        deletions: pr.deletions || 0,
        number: pr.number,
        html_url: pr.html_url,
      }));
      setPullRequests(prs);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to fetch pull requests');
    } finally {
      setLoadingPRs(false);
    }
  };

  const fetchDiff = async (pr: PRDisplay, repo: Repository) => {
    setLoadingDiff(true);
    try {
      const data = await apiClient.get<{ diff: string }>(`/api/v1/repos/${repo.id}/pulls/${pr.number}/diff`);
      setDiff(data.diff || '');
    } catch {
      toast.error('Failed to load diff from GitHub');
      setDiff('');
    } finally {
      setLoadingDiff(false);
    }
  };

  const handleSelectPR = (pr: PRDisplay) => {
    setSelected(pr);
    setDiff(null);
    setActiveTab('overview');
  };

  const handleAIReview = async (pr: PRDisplay) => {
    if (!pr || reviewing || !selectedRepo) return;
    setReviewing(true);
    try {
      const review = await apiClient.post<{
        summary: string;
        potential_issues: string[];
        refactoring_suggestions: string[];
        security_warnings: string[];
        performance_notes: string[];
      }>('/api/v1/pr-review', {
        repository_id: selectedRepo.id,
        pr_title: pr.title,
        pr_description: '',
        pr_number: pr.number,
        pull_request_diff: '',
      });

      const suggestedChanges = [
        ...review.potential_issues,
        ...review.refactoring_suggestions,
        ...review.security_warnings,
        ...review.performance_notes,
      ].filter(Boolean);

      const updatedPR = { ...pr, aiSummary: review.summary, suggestedChanges };
      setPullRequests(prev => prev.map(p => p.id === pr.id ? updatedPR : p));
      setSelected(updatedPR);
      toast.success('AI review complete');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'AI review failed');
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Pull Requests</h1>
        <p className="mt-1 text-sm text-muted-foreground">AI-powered code reviews with real diff preview</p>
      </div>

      {/* Controls */}
      {!loading && repos.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setRepoDropdownOpen(v => !v)}
              className="flex items-center gap-2 h-9 rounded-md border border-input bg-accent px-3 text-sm outline-none hover:border-primary transition-colors"
            >
              <Github className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="max-w-[200px] truncate text-foreground">
                {selectedRepo ? selectedRepo.full_name : "Select repository"}
              </span>
              <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform shrink-0 ${repoDropdownOpen ? "rotate-180" : ""}`} />
            </button>
            {repoDropdownOpen && (
              <div className="absolute top-full mt-1 left-0 z-50 w-64 rounded-lg border border-border bg-card shadow-lg overflow-hidden animate-slide-up">
                {repos.map(r => (
                  <button
                    key={r.id}
                    onClick={() => { setSelectedRepo(r); setRepoDropdownOpen(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent transition-colors"
                  >
                    <span className="flex-1 truncate text-card-foreground">{r.full_name}</span>
                    {selectedRepo?.id === r.id && <Check className="h-3.5 w-3.5 text-primary shrink-0" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex rounded-md border border-border overflow-hidden text-sm">
            {(['open', 'closed', 'all'] as const).map(s => (
              <button
                key={s}
                onClick={() => setStateFilter(s)}
                className={`px-3 py-1.5 capitalize transition-colors ${stateFilter === s
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-accent text-muted-foreground hover:text-foreground'
                  }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : repos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 rounded-xl border border-dashed border-border">
          <GitPullRequest className="h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium">No repositories connected</p>
          <p className="mt-1 text-xs text-muted-foreground">Connect a repository first to view pull requests.</p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          {/* PR List */}
          <div className="lg:col-span-2 space-y-2">
            {loadingPRs ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : pullRequests.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 rounded-xl border border-dashed border-border">
                <GitPullRequest className="h-8 w-8 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">No {stateFilter === 'all' ? '' : stateFilter} pull requests</p>
              </div>
            ) : (
              pullRequests.map((pr) => (
                <button
                  key={pr.id}
                  onClick={() => handleSelectPR(pr)}
                  className={`w-full rounded-xl border p-4 text-left transition-colors ${selected?.id === pr.id
                    ? "border-primary bg-primary/5"
                    : "border-border bg-card hover:border-primary/30"
                    }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 min-w-0">
                      {pr.authorAvatar ? (
                        <img src={pr.authorAvatar} alt={pr.author} className="mt-0.5 h-5 w-5 rounded-full shrink-0" />
                      ) : (
                        <GitPullRequest className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-card-foreground truncate">#{pr.number} {pr.title}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">{pr.author} · {pr.createdAt}</p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                  </div>
                  <div className="mt-2 flex items-center gap-3">
                    <StatusBadge status={pr.status} variant={prStatusVariant(pr.status)} />
                    <span className="flex items-center gap-1 text-xs text-green-500"><Plus className="h-3 w-3" />{pr.additions}</span>
                    <span className="flex items-center gap-1 text-xs text-red-500"><Minus className="h-3 w-3" />{pr.deletions}</span>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* PR Detail */}
          <div className="lg:col-span-3">
            {selected ? (
              <div className="rounded-xl border border-border bg-card overflow-hidden">
                {/* PR header */}
                <div className="border-b border-border p-5">
                  <div className="flex items-start gap-3">
                    {selected.authorAvatar && (
                      <img src={selected.authorAvatar} alt={selected.author} className="h-8 w-8 rounded-full shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <h2 className="text-base font-semibold text-card-foreground">#{selected.number} {selected.title}</h2>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        by {selected.author} · {selected.createdAt} · {selected.repository}
                      </p>
                      <div className="mt-2 flex items-center gap-3">
                        <StatusBadge status={selected.status} variant={prStatusVariant(selected.status)} />
                        <span className="text-xs text-green-500">+{selected.additions}</span>
                        <span className="text-xs text-red-500">-{selected.deletions}</span>
                      </div>
                    </div>
                    {selected.html_url && (
                      <a href={selected.html_url} target="_blank" rel="noopener noreferrer"
                        className="shrink-0 flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-accent transition-colors">
                        <Github className="h-3 w-3" /> GitHub
                      </a>
                    )}
                  </div>

                  {/* Tab bar */}
                  <div className="mt-4 flex gap-1">
                    <button
                      onClick={() => setActiveTab('overview')}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'overview' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-accent'}`}
                    >
                      <MessageSquare className="h-3.5 w-3.5" />
                      Overview
                    </button>
                    <button
                      onClick={() => setActiveTab('diff')}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'diff' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-accent'}`}
                    >
                      <Code2 className="h-3.5 w-3.5" />
                      Diff
                    </button>
                  </div>
                </div>

                {/* Tab content */}
                <div className="p-5">
                  {activeTab === 'overview' ? (
                    <div className="space-y-5">
                      {selected.aiSummary ? (
                        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                          <p className="text-xs font-medium text-primary mb-2">AI Review Summary</p>
                          <p className="text-sm text-card-foreground leading-relaxed">{selected.aiSummary}</p>
                        </div>
                      ) : (
                        <div className="rounded-lg border border-border bg-muted p-4 text-center">
                          <GitMerge className="h-6 w-6 mx-auto text-muted-foreground mb-2" />
                          <p className="text-sm text-muted-foreground">Run AI Review to analyze this pull request</p>
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

                      <div className="flex gap-3 pt-1">
                        <Button className="gap-2" onClick={() => handleAIReview(selected)} disabled={reviewing}>
                          {reviewing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                          {reviewing ? 'Reviewing...' : 'AI Review'}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      {loadingDiff ? (
                        <div className="flex items-center justify-center py-12">
                          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                          <span className="ml-2 text-sm text-muted-foreground">Loading diff from GitHub...</span>
                        </div>
                      ) : (
                        <DiffViewer diff={diff || ''} maxHeightPx={520} />
                      )}
                    </div>
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
