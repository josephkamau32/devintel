import { useState, useEffect } from "react";
import { Plus, Search, RefreshCw, Eye, Trash2, Github, Loader2, AlertCircle, Check } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import type { Repository, GitHubRepo } from "@/lib/types";

const statusVariant = (s?: string) =>
  s === "completed" ? "success" : s === "in_progress" ? "warning" : "default";

const statusLabel = (s?: string) =>
  s === "completed" ? "Indexed" : s === "in_progress" ? "Indexing..." : "Not Indexed";

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [githubRepos, setGithubRepos] = useState<GitHubRepo[]>([]);
  const [loadingGH, setLoadingGH] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [indexingId, setIndexingId] = useState<string | null>(null);

  const fetchRepos = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos');
      setRepos(data.repositories || []);
    } catch (err) {
      console.error('Failed to fetch repos:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRepos(); }, []);

  const fetchGithubRepos = async () => {
    setLoadingGH(true);
    try {
      const data = await apiClient.get<{ repositories: GitHubRepo[] }>('/api/v1/repos/github?per_page=50');
      setGithubRepos(data.repositories || []);
    } catch (err) {
      console.error('Failed to fetch GitHub repos:', err);
      toast.error('Failed to fetch your GitHub repositories');
    } finally {
      setLoadingGH(false);
    }
  };

  const handleOpenModal = () => {
    setShowModal(true);
    fetchGithubRepos();
  };

  const connectRepo = async (fullName: string, url: string) => {
    setConnecting(true);
    try {
      const name = fullName.split('/').pop() || fullName;
      await apiClient.post('/api/v1/repos', {
        name,
        full_name: fullName,
        url,
      });
      toast.success(`Connected ${fullName}`);
      setShowModal(false);
      setRepoUrl("");
      await fetchRepos();
    } catch (err: any) {
      toast.error(err.message || 'Failed to connect repository');
    } finally {
      setConnecting(false);
    }
  };

  const handleConnectByUrl = () => {
    if (!repoUrl.trim()) return;
    // Extract owner/repo from URL
    const match = repoUrl.match(/github\.com\/([^/]+\/[^/]+)/);
    if (match) {
      connectRepo(match[1].replace(/\.git$/, ''), repoUrl.trim());
    } else {
      toast.error('Invalid GitHub URL. Expected: https://github.com/owner/repo');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete repository "${name}"? This cannot be undone.`)) return;
    setDeletingId(id);
    try {
      await apiClient.delete(`/api/v1/repos/${id}`);
      toast.success(`Deleted ${name}`);
      setRepos(prev => prev.filter(r => r.id !== id));
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete repository');
    } finally {
      setDeletingId(null);
    }
  };

  const handleIndex = async (id: string) => {
    setIndexingId(id);
    try {
      await apiClient.post('/api/v1/repos/index', { repository_id: id });
      toast.success('Indexing started');
      await fetchRepos();
    } catch (err: any) {
      toast.error(err.message || 'Failed to start indexing');
    } finally {
      setIndexingId(null);
    }
  };

  const filtered = repos.filter((r) => (r.full_name || r.name).toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My Repositories</h1>
          <p className="mt-1 text-sm text-muted-foreground">Manage and index your GitHub repositories</p>
        </div>
        <Button className="gap-2" onClick={handleOpenModal}>
          <Github className="h-4 w-4" /> Connect Repository
        </Button>
      </div>

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

      <div className="overflow-hidden rounded-xl border border-border">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <Github className="h-10 w-10 text-muted-foreground" />
            <p className="mt-3 text-sm text-muted-foreground">
              {repos.length === 0 ? "No repositories connected yet" : "No matching repositories"}
            </p>
            {repos.length === 0 && (
              <Button size="sm" className="mt-3 gap-2" onClick={handleOpenModal}>
                <Plus className="h-3 w-3" /> Connect your first repo
              </Button>
            )}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Repository</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="hidden px-4 py-3 text-left font-medium text-muted-foreground sm:table-cell">Language</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((repo) => (
                <tr key={repo.id} className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-foreground">{repo.name}</p>
                      <p className="text-xs text-muted-foreground">{repo.full_name}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={statusLabel(repo.indexed_status)} variant={statusVariant(repo.indexed_status)} />
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">{repo.language || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleIndex(repo.id)}
                        disabled={indexingId === repo.id}
                        className="rounded p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors disabled:opacity-50"
                        title="Re-index"
                      >
                        {indexingId === repo.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => handleDelete(repo.id, repo.full_name)}
                        disabled={deletingId === repo.id}
                        className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors disabled:opacity-50"
                        title="Delete"
                      >
                        {deletingId === repo.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Connect Repository Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg animate-slide-up max-h-[80vh] flex flex-col">
            <h2 className="text-lg font-semibold text-card-foreground">Connect GitHub Repository</h2>

            {/* URL input */}
            <div className="mt-4">
              <label className="text-sm font-medium text-foreground">Repository URL</label>
              <div className="flex gap-2 mt-1.5">
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo"
                  className="h-9 flex-1 rounded-md border border-input bg-accent px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
                />
                <Button size="sm" onClick={handleConnectByUrl} disabled={connecting || !repoUrl.trim()}>
                  {connecting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Connect'}
                </Button>
              </div>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3 my-4">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs text-muted-foreground">or select from your GitHub</span>
              <div className="h-px flex-1 bg-border" />
            </div>

            {/* GitHub repos list */}
            <div className="flex-1 overflow-auto space-y-1 min-h-0">
              {loadingGH ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : githubRepos.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No repositories found</p>
              ) : (
                githubRepos.map((ghRepo) => {
                  const alreadyConnected = repos.some(r => r.full_name === ghRepo.full_name);
                  return (
                    <button
                      key={ghRepo.id}
                      disabled={alreadyConnected || connecting}
                      onClick={() => connectRepo(ghRepo.full_name, ghRepo.html_url)}
                      className={`w-full flex items-center gap-3 rounded-lg p-3 text-left transition-colors ${alreadyConnected
                          ? 'opacity-50 cursor-not-allowed bg-accent/30'
                          : 'hover:bg-accent'
                        }`}
                    >
                      <Github className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-card-foreground truncate">{ghRepo.full_name}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {ghRepo.language || 'Unknown'} · {ghRepo.stargazers_count} ★{ghRepo.private ? ' · Private' : ''}
                        </p>
                      </div>
                      {alreadyConnected && (
                        <span className="text-xs text-success flex items-center gap-1"><Check className="h-3 w-3" /> Added</span>
                      )}
                    </button>
                  );
                })
              )}
            </div>

            <div className="mt-4 flex justify-end">
              <Button variant="outline" onClick={() => { setShowModal(false); setRepoUrl(""); }}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
