import { useState, useMemo, useEffect } from "react";
import { toast } from "sonner";
import {
  Search,
  RefreshCw,
  Trash2,
  Github,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Lock,
  Star,
  FolderGit2,
} from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { useRepositories } from "@/hooks/useRepositories";
import type { RepoResponse, GitHubRepo } from "@/lib/api";

// ─── Helpers ────────────────────────────────────────────────────────────────────

function repoStatus(r: RepoResponse): "indexed" | "indexing" | "error" | "not_indexed" {
  if (r.indexing_error) return "error";
  if (r.indexed_status) return "indexed";
  if (r.indexing_progress > 0) return "indexing";
  return "not_indexed";
}

const statusConfig = {
  indexed: { label: "Indexed", variant: "success" as const, icon: CheckCircle2 },
  indexing: { label: "Indexing…", variant: "warning" as const, icon: Loader2 },
  error: { label: "Error", variant: "error" as const, icon: AlertCircle },
  not_indexed: { label: "Not Indexed", variant: "default" as const, icon: null },
};

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ─── Page ───────────────────────────────────────────────────────────────────────

export default function RepositoriesPage() {
  const {
    repos,
    loading,
    error,
    refresh,
    githubRepos,
    githubLoading,
    githubError,
    loadGithubRepos,
    connectAndIndex,
    removeRepo,
    reindexRepo,
  } = useRepositories();

  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [ghSearch, setGhSearch] = useState("");
  const [connecting, setConnecting] = useState<string | null>(null); // full_name being connected
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [reindexingId, setReindexingId] = useState<string | null>(null);

  // Close modal on Escape key
  useEffect(() => {
    if (!showModal) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowModal(false);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [showModal]);

  const filtered = useMemo(
    () => repos.filter((r) => r.full_name.toLowerCase().includes(search.toLowerCase())),
    [repos, search],
  );

  // GitHub repos filtered by search AND not already connected
  const connectedNames = useMemo(() => new Set(repos.map((r) => r.full_name)), [repos]);
  const filteredGhRepos = useMemo(
    () =>
      githubRepos
        .filter((r) => r.full_name.toLowerCase().includes(ghSearch.toLowerCase()))
        .filter((r) => !connectedNames.has(r.full_name)),
    [githubRepos, ghSearch, connectedNames],
  );

  // ─── Handlers ────────────────────────────────────────────────────────────────

  const handleOpenModal = () => {
    setShowModal(true);
    setGhSearch("");
    loadGithubRepos();
  };

  const handleConnect = async (ghRepo: GitHubRepo) => {
    setConnecting(ghRepo.full_name);
    try {
      await connectAndIndex(ghRepo);
      toast.success(`Connected ${ghRepo.full_name} — indexing started`);
      setShowModal(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      const msg = err?.response?.data?.detail || "Failed to connect repository";
      toast.error(msg);
    } finally {
      setConnecting(null);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    setDeletingId(id);
    try {
      await removeRepo(id);
      toast.success(`Removed ${name}`);
    } catch {
      toast.error("Failed to delete repository");
    } finally {
      setDeletingId(null);
    }
  };

  const handleReindex = async (id: string) => {
    setReindexingId(id);
    try {
      await reindexRepo(id);
      toast.success("Re-indexing started");
    } catch {
      toast.error("Failed to start re-indexing");
    } finally {
      setReindexingId(null);
    }
  };

  // ─── Loading skeleton ────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-7 w-48 animate-pulse rounded bg-muted" />
            <div className="mt-2 h-4 w-72 animate-pulse rounded bg-muted" />
          </div>
          <div className="h-9 w-44 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-9 w-72 animate-pulse rounded bg-muted" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl border border-border bg-muted/30" />
          ))}
        </div>
      </div>
    );
  }

  // ─── Error state ─────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <h2 className="text-lg font-semibold">Failed to load repositories</h2>
        <p className="max-w-md text-sm text-muted-foreground">{error}</p>
        <Button onClick={refresh} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My Repositories</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage and index your GitHub repositories
          </p>
        </div>
        <Button className="gap-2" onClick={handleOpenModal}>
          <Github className="h-4 w-4" /> Connect Repository
        </Button>
      </div>

      {/* Search */}
      {repos.length > 0 && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search repositories..."
            className="h-9 w-full rounded-md border border-input bg-accent pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
          />
        </div>
      )}

      {/* Empty State */}
      {repos.length === 0 && (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border bg-card py-16 text-center">
          <FolderGit2 className="h-12 w-12 text-muted-foreground/50" />
          <h2 className="text-lg font-semibold text-card-foreground">No repositories connected</h2>
          <p className="max-w-md text-sm text-muted-foreground">
            Connect your GitHub repositories to start indexing and chatting with your code using AI.
          </p>
          <Button className="gap-2" onClick={handleOpenModal}>
            <Github className="h-4 w-4" /> Connect Your First Repository
          </Button>
        </div>
      )}

      {/* Repository Table */}
      {filtered.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Repository</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="hidden px-4 py-3 text-left font-medium text-muted-foreground sm:table-cell">Language</th>
                <th className="hidden px-4 py-3 text-left font-medium text-muted-foreground md:table-cell">Last Indexed</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((repo) => {
                const s = repoStatus(repo);
                const cfg = statusConfig[s];

                return (
                  <tr key={repo.id} className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors">
                    {/* Name */}
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-foreground">{repo.repo_name}</p>
                        <p className="text-xs text-muted-foreground">{repo.full_name}</p>
                      </div>
                    </td>

                    {/* Status + Progress */}
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1.5">
                        <StatusBadge status={cfg.label} variant={cfg.variant} />
                        {s === "indexing" && (
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                              <div
                                className="h-full rounded-full bg-primary transition-all duration-500"
                                style={{ width: `${repo.indexing_progress}%` }}
                              />
                            </div>
                            <span className="text-xs tabular-nums text-muted-foreground">
                              {repo.indexing_progress}%
                            </span>
                          </div>
                        )}
                        {s === "error" && repo.indexing_error && (
                          <p className="max-w-[200px] truncate text-xs text-destructive" title={repo.indexing_error}>
                            {repo.indexing_error}
                          </p>
                        )}
                      </div>
                    </td>

                    {/* Language */}
                    <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                      {repo.language || "—"}
                    </td>

                    {/* Last Indexed */}
                    <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">
                      {timeAgo(repo.last_indexed_at)}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="rounded p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors disabled:opacity-40"
                          title="Re-index"
                          disabled={s === "indexing" || reindexingId === repo.id}
                          onClick={() => handleReindex(repo.id)}
                        >
                          <RefreshCw className={`h-4 w-4 ${reindexingId === repo.id ? "animate-spin" : ""}`} />
                        </button>
                        <button
                          className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors disabled:opacity-40"
                          title="Delete"
                          disabled={deletingId === repo.id}
                          onClick={() => handleDelete(repo.id, repo.full_name)}
                        >
                          {deletingId === repo.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* No search results */}
      {repos.length > 0 && filtered.length === 0 && search && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No repositories matching "{search}"
        </p>
      )}

      {/* ─── Connect Repository Modal ────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg animate-slide-up">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-card-foreground">Connect GitHub Repository</h2>
              <button
                onClick={() => setShowModal(false)}
                className="rounded p-1 text-muted-foreground hover:text-foreground transition-colors"
              >
                ✕
              </button>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Select a repository from your GitHub account to connect and index.
            </p>

            {/* Search GitHub repos */}
            <div className="relative mt-4">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={ghSearch}
                onChange={(e) => setGhSearch(e.target.value)}
                placeholder="Filter repositories..."
                className="h-9 w-full rounded-md border border-input bg-accent pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
              />
            </div>

            {/* GitHub repos list */}
            <div className="mt-4 max-h-80 overflow-y-auto rounded-lg border border-border">
              {githubLoading && (
                <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Loading your repositories...</span>
                </div>
              )}

              {githubError && (
                <div className="flex flex-col items-center gap-2 py-12 text-center">
                  <AlertCircle className="h-6 w-6 text-destructive" />
                  <p className="text-sm text-destructive">{githubError}</p>
                  <Button variant="outline" size="sm" onClick={loadGithubRepos}>
                    Retry
                  </Button>
                </div>
              )}

              {!githubLoading && !githubError && filteredGhRepos.length === 0 && (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  {githubRepos.length > 0
                    ? "All matching repositories are already connected."
                    : "No repositories found on your GitHub account."}
                </div>
              )}

              {!githubLoading &&
                !githubError &&
                filteredGhRepos.map((ghRepo) => (
                  <div
                    key={ghRepo.full_name}
                    className="flex items-center justify-between border-b border-border px-4 py-3 last:border-0 hover:bg-accent/50 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="truncate font-medium text-sm text-foreground">{ghRepo.full_name}</p>
                        {ghRepo.private && <Lock className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
                      </div>
                      <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                        {ghRepo.language && <span>{ghRepo.language}</span>}
                        {ghRepo.stars > 0 && (
                          <span className="flex items-center gap-0.5">
                            <Star className="h-3 w-3" /> {ghRepo.stars}
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={connecting === ghRepo.full_name}
                      onClick={() => handleConnect(ghRepo)}
                      className="ml-3 shrink-0"
                    >
                      {connecting === ghRepo.full_name ? (
                        <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                      ) : null}
                      {connecting === ghRepo.full_name ? "Connecting…" : "Connect & Index"}
                    </Button>
                  </div>
                ))}
            </div>

            {/* Footer */}
            <div className="mt-4 flex justify-end">
              <Button variant="outline" onClick={() => setShowModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
