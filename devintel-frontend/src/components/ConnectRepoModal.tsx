import React, { useState } from 'react';
import { Modal } from './ui/Modal';
import { useGitHubRepositories, connectRepository } from '../hooks/useRepositories';
import { Loader2, Plus, Check, Search } from 'lucide-react';
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
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm animate-slide-down">
            {error}
          </div>
        )}

        {/* Search filter */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter repositories…"
            className="w-full pl-9 pr-4 py-2.5 text-sm bg-slate-800/60 border border-slate-700 rounded-lg text-white placeholder-slate-500 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 transition-all"
          />
        </div>

        {isLoading && page === 1 ? (
          <div className="flex flex-col items-center justify-center p-10 gap-3">
            <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
            <p className="text-sm text-slate-500">Loading your repositories…</p>
          </div>
        ) : isError ? (
          <div className="p-6 text-center">
            <p className="text-red-400 mb-2">Failed to load repositories.</p>
            <p className="text-sm text-slate-500">Make sure your GitHub account is connected.</p>
          </div>
        ) : filteredRepos.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            {filter ? 'No repositories match your search.' : 'No repositories found on your GitHub account.'}
          </div>
        ) : (
          <div className="space-y-2 max-h-[55vh] overflow-y-auto pr-1">
            {filteredRepos.map((repo: GitHubRepository) => {
              const isConnected = connectedRepoFullNames.includes(repo.full_name);
              const isConnecting = connectingFullName === repo.full_name;

              return (
                <div 
                  key={repo.full_name}
                  className="flex items-center justify-between p-4 bg-slate-800/30 border border-slate-800 rounded-xl hover:bg-slate-800/60 hover:border-slate-700 transition-all duration-200"
                >
                  <div className="min-w-0 mr-3">
                    <h4 className="font-medium text-white flex items-center space-x-2">
                      <span className="truncate">{repo.repo_name}</span>
                      {repo.private && (
                        <span className="flex-shrink-0 px-2 py-0.5 text-[10px] bg-slate-700 text-slate-300 rounded-full font-medium">
                          Private
                        </span>
                      )}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5 truncate">{repo.full_name}</p>
                  </div>
                  
                  <button
                    onClick={() => handleConnect(repo)}
                    disabled={isConnected || isConnecting}
                    className={`flex-shrink-0 flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium text-xs transition-all duration-200 ${
                      isConnected
                        ? 'bg-emerald-500/10 text-emerald-400 cursor-default border border-emerald-500/20'
                        : isConnecting
                        ? 'bg-violet-600/50 text-white cursor-wait'
                        : 'bg-violet-600 hover:bg-violet-500 text-white shadow-sm'
                    }`}
                  >
                    {isConnected ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Connected</span>
                      </>
                    ) : isConnecting ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
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
        
        <div className="flex justify-between items-center pt-4 border-t border-slate-800">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 transition-colors rounded-lg hover:bg-slate-800"
          >
            ← Previous
          </button>
          <span className="text-xs text-slate-500 font-medium">Page {page}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={githubRepositories.length < 30 || isLoading}
            className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 transition-colors rounded-lg hover:bg-slate-800"
          >
            Next →
          </button>
        </div>
      </div>
    </Modal>
  );
};
