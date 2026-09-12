import React, { useState } from 'react';
import { Modal } from './ui/Modal';
import { useGitHubRepositories, connectRepository, indexRepository } from '../hooks/useRepositories';
import { Loader2, Plus, Check, Search, AlertCircle, FolderGit2, Github, Link } from 'lucide-react';
import { GitHubRepository } from '../types/repository';
import { AxiosError } from 'axios';

interface ValidationError {
  field: string;
  message: string;
}

interface ConnectRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: () => void;
  connectedRepoFullNames: string[];
}

type Tab = 'github' | 'url';

export const ConnectRepoModal: React.FC<ConnectRepoModalProps> = ({ 
  isOpen, 
  onClose, 
  onConnect,
  connectedRepoFullNames 
}) => {
  const [tab, setTab] = useState<Tab>('github');
  const [page, setPage] = useState(1);
  const { githubRepositories, isLoading, isError } = useGitHubRepositories(page, 30);
  const [connectingFullName, setConnectingFullName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  // URL-based connection state
  const [urlInput, setUrlInput] = useState('');
  const [urlConnecting, setUrlConnecting] = useState(false);

  const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

  const handleConnect = async (repo: GitHubRepository) => {
    setConnectingFullName(repo.full_name);
    setError(null);
    try {
      const created = await connectRepository(repo);
      // Immediately trigger indexing — reuses the already-working code path used in
      // RepositoriesPage, DashboardPage, and SettingsTab. Fresh repos have
      // indexing_progress=0 so the backend mutex check (0 < 0 < 100) is false → safe.
      try {
        await indexRepository(created.id);
      } catch (_indexErr) {
        // Non-fatal: repo is connected, user can retry from the card.
        console.warn('Auto-index after connect failed:', _indexErr);
      }
      onConnect();
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string; errors?: ValidationError[] }>;
      const detail = axiosErr.response?.data?.detail;
      const errors = axiosErr.response?.data?.errors;
      let message = 'Failed to connect repository';
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(errors) && errors.length > 0) {
        message = errors.map((e: ValidationError) => `${e.field}: ${e.message}`).join(', ');
      }
      setError(message);
    } finally {
      setConnectingFullName(null);
    }
  };

  const handleUrlConnect = async () => {
    const raw = urlInput.trim();
    if (!raw) return;

    // Accept full GitHub URL or owner/repo format
    let fullName = raw;
    const urlMatch = raw.match(/github\.com\/([^/]+\/[^/]+?)(?:\.git)?(?:\/?$)/);
    if (urlMatch) fullName = urlMatch[1];

    const parts = fullName.split('/');
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      setError('Please enter a valid GitHub URL or owner/repo (e.g. "facebook/react")');
      return;
    }
    const [, repoName] = parts;

    setUrlConnecting(true);
    setError(null);
    try {
      const repo: GitHubRepository = {
        repo_name: repoName,
        full_name: fullName,
        description: null,
        url: `https://github.com/${fullName}`,
        clone_url: `https://github.com/${fullName}.git`,
        stars: 0,
        language: null,
        private: false,
        default_branch: 'main',
      };
      const created = await connectRepository(repo);
      try {
        await indexRepository(created.id);
      } catch (_indexErr) {
        console.warn('Auto-index after URL-connect failed:', _indexErr);
      }
      setUrlInput('');
      onConnect();
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      const detail = axiosErr.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to connect repository');
    } finally {
      setUrlConnecting(false);
    }
  };

  const filteredRepos = filter
    ? githubRepositories.filter((r) =>
        r.full_name.toLowerCase().includes(filter.toLowerCase()) ||
        r.repo_name.toLowerCase().includes(filter.toLowerCase())
      )
    : githubRepositories;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Connect Repository">
      <div className="space-y-4">
        {/* Tab selector */}
        <div className="flex rounded-lg bg-surface-2 p-1 gap-1">
          <button
            onClick={() => { setTab('github'); setError(null); }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-all ${
              tab === 'github'
                ? 'bg-surface-0 text-text-primary shadow-subtle'
                : 'text-text-tertiary hover:text-text-secondary'
            }`}
          >
            <Github className="h-4 w-4" />
            GitHub
          </button>
          <button
            onClick={() => { setTab('url'); setError(null); }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-all ${
              tab === 'url'
                ? 'bg-surface-0 text-text-primary shadow-subtle'
                : 'text-text-tertiary hover:text-text-secondary'
            }`}
          >
            <Link className="h-4 w-4" />
            By URL
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-status-error-muted border border-status-error/20 text-status-error rounded-lg text-sm animate-slide-down">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* ── GitHub tab ── */}
        {tab === 'github' && (
          <>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-quaternary" />
              <input
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter repositories…"
                className="w-full pl-9 pr-4 py-2.5 text-sm bg-surface-3 border border-border-medium rounded-lg text-text-primary placeholder-text-quaternary outline-none focus:border-brand-500 focus:shadow-focus-ring transition-all"
              />
            </div>

            {isLoading && page === 1 ? (
              <div className="flex flex-col items-center justify-center p-10 gap-3">
                <Loader2 className="w-6 h-6 text-brand-400 animate-spin-slow" />
                <p className="text-body-sm text-text-tertiary">Loading your repositories…</p>
              </div>
            ) : isError ? (
              /* GitHub not connected — show clear CTA */
              <div className="p-8 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-surface-3 border border-border">
                  <Github className="h-6 w-6 text-text-quaternary" />
                </div>
                <p className="text-sm font-medium text-text-primary mb-1">
                  GitHub account not connected
                </p>
                <p className="text-body-sm text-text-tertiary mb-5">
                  Connect your GitHub account to browse and import repositories, or use the{' '}
                  <button
                    onClick={() => setTab('url')}
                    className="text-brand-400 underline underline-offset-2 hover:text-brand-300"
                  >
                    By URL
                  </button>{' '}
                  tab to connect any public repository without linking GitHub.
                </p>
                <a
                  href={`${apiBase}/api/v1/auth/github`}
                  className="inline-flex items-center gap-2 bg-[#24292e] hover:bg-[#1b1f23] text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-all shadow-subtle"
                >
                  <Github className="h-4 w-4" />
                  Connect GitHub Account
                </a>
              </div>
            ) : filteredRepos.length === 0 ? (
              <div className="p-8 text-center">
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-surface-3 border border-border">
                  <FolderGit2 className="h-5 w-5 text-text-quaternary" />
                </div>
                <p className="text-sm text-text-tertiary">
                  {filter ? 'No repositories match your search.' : 'No repositories found on your GitHub account.'}
                </p>
              </div>
            ) : (
              <div className="space-y-1.5 max-h-[55vh] overflow-y-auto pr-1">
                {filteredRepos.map((repo: GitHubRepository) => {
                  const isConnected = connectedRepoFullNames.includes(repo.full_name);
                  const isConnecting = connectingFullName === repo.full_name;

                  return (
                    <div 
                      key={repo.full_name}
                      className="flex items-center justify-between p-3.5 bg-surface-2 border border-border rounded-lg hover:bg-surface-3 hover:border-border-medium transition-all duration-150"
                    >
                      <div className="min-w-0 mr-3">
                        <h4 className="text-sm font-medium text-text-primary flex items-center gap-2">
                          <span className="truncate">{repo.repo_name}</span>
                          {repo.private && (
                            <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] bg-surface-4 text-text-quaternary rounded font-medium border border-border">
                              Private
                            </span>
                          )}
                        </h4>
                        <p className="text-xs text-text-quaternary mt-0.5 truncate">
                          {repo.full_name}
                        </p>
                      </div>
                      
                      <button
                        onClick={() => handleConnect(repo)}
                        disabled={isConnected || isConnecting}
                        className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium text-xs transition-all duration-150 ${
                          isConnected
                            ? 'bg-status-success-muted text-status-success cursor-default border border-status-success/20'
                            : isConnecting
                            ? 'bg-brand-600/50 text-white cursor-wait'
                            : 'bg-brand-600 hover:bg-brand-500 text-white shadow-subtle'
                        }`}
                      >
                        {isConnected ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Connected</span>
                          </>
                        ) : isConnecting ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin-slow" />
                            <span>Connecting…</span>
                          </>
                        ) : (
                          <>
                            <Plus className="w-3.5 h-3.5" />
                            <span>Connect</span>
                          </>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
            
            {!isError && (
              <div className="flex justify-between items-center pt-3 border-t border-border">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1 || isLoading}
                  className="px-3 py-1.5 text-sm font-medium text-text-tertiary hover:text-text-primary disabled:opacity-30 transition-colors rounded-md hover:bg-surface-3"
                >
                  ← Previous
                </button>
                <span className="text-xs text-text-quaternary font-medium">Page {page}</span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={githubRepositories.length < 30 || isLoading}
                  className="px-3 py-1.5 text-sm font-medium text-text-tertiary hover:text-text-primary disabled:opacity-30 transition-colors rounded-md hover:bg-surface-3"
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}

        {/* ── By URL tab ── */}
        {tab === 'url' && (
          <div className="space-y-4">
            <p className="text-sm text-text-tertiary">
              Connect any public GitHub repository without linking your GitHub account.
              Enter the full URL or <span className="text-text-secondary font-medium">owner/repo</span> format.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleUrlConnect()}
                placeholder="https://github.com/owner/repo  or  owner/repo"
                className="flex-1 px-3.5 py-2.5 text-sm bg-surface-3 border border-border-medium rounded-lg text-text-primary placeholder-text-quaternary outline-none focus:border-brand-500 focus:shadow-focus-ring transition-all"
              />
              <button
                onClick={handleUrlConnect}
                disabled={urlConnecting || !urlInput.trim()}
                className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium bg-brand-600 hover:bg-brand-500 text-white shadow-subtle transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {urlConnecting ? (
                  <Loader2 className="w-4 h-4 animate-spin-slow" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                {urlConnecting ? 'Connecting…' : 'Connect'}
              </button>
            </div>
            <p className="text-xs text-text-quaternary">
              Example:{' '}
              <code className="bg-surface-3 px-1.5 py-0.5 rounded text-text-tertiary">facebook/react</code>
              {' '}or{' '}
              <code className="bg-surface-3 px-1.5 py-0.5 rounded text-text-tertiary">https://github.com/torvalds/linux</code>
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
};


