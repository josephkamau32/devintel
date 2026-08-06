import React, { useState } from 'react';
import { Modal } from './ui/Modal';
import { useGitHubRepositories, connectRepository } from '../hooks/useRepositories';
import { Loader2, Plus, Check, Search, AlertCircle, FolderGit2 } from 'lucide-react';
import { GitHubRepository } from '../types/repository';

interface ConnectRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: () => void;
  connectedRepoFullNames: string[];
}

export const ConnectRepoModal: React.FC<ConnectRepoModalProps> = ({ 
  isOpen, 
  onClose, 
  onConnect,
  connectedRepoFullNames 
}) => {
  const [page, setPage] = useState(1);
  const { githubRepositories, isLoading, isError } = useGitHubRepositories(page, 30);
  const [connectingFullName, setConnectingFullName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  const handleConnect = async (repo: GitHubRepository) => {
    setConnectingFullName(repo.full_name);
    setError(null);
    try {
      await connectRepository(repo);
      onConnect();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const errors = err.response?.data?.errors;
      let message = 'Failed to connect repository';
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(errors) && errors.length > 0) {
        message = errors.map((e: any) => `${e.field}: ${e.message}`).join(', ');
      }
      setError(message);
    } finally {
      setConnectingFullName(null);
    }
  };

  const filteredRepos = filter
    ? githubRepositories.filter((r) =>
        r.full_name.toLowerCase().includes(filter.toLowerCase()) ||
        r.repo_name.toLowerCase().includes(filter.toLowerCase())
      )
    : githubRepositories;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Connect GitHub Repository">
      <div className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-status-error-muted border border-status-error/20 text-status-error rounded-lg text-sm animate-slide-down">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Search filter */}
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
          <div className="p-8 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-status-error-muted border border-status-error/20">
              <AlertCircle className="h-5 w-5 text-status-error" />
            </div>
            <p className="text-sm font-medium text-status-error mb-1">Failed to load repositories</p>
            <p className="text-body-sm text-text-tertiary">Make sure your GitHub account is connected.</p>
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
        
        <div className="flex justify-between items-center pt-3 border-t border-border">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className="px-3 py-1.5 text-sm font-medium text-text-tertiary hover:text-text-primary disabled:opacity-30 disabled:hover:text-text-tertiary transition-colors rounded-md hover:bg-surface-3"
          >
            ← Previous
          </button>
          <span className="text-xs text-text-quaternary font-medium">Page {page}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={githubRepositories.length < 30 || isLoading}
            className="px-3 py-1.5 text-sm font-medium text-text-tertiary hover:text-text-primary disabled:opacity-30 disabled:hover:text-text-tertiary transition-colors rounded-md hover:bg-surface-3"
          >
            Next →
          </button>
        </div>
      </div>
    </Modal>
  );
};
