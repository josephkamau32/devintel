import React, { useState } from 'react';
import { Modal } from './ui/Modal';
import { useGitHubRepositories, connectRepository } from '../hooks/useRepositories';
import { Loader2, Plus, Check } from 'lucide-react';
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Connect GitHub Repository">
      <div className="space-y-4">
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        {isLoading && page === 1 ? (
          <div className="flex justify-center p-8">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : isError ? (
          <div className="p-4 text-center text-red-400">
            Failed to load repositories. Please make sure your GitHub account is connected.
          </div>
        ) : githubRepositories.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No repositories found on your GitHub account.
          </div>
        ) : (
          <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-2">
            {githubRepositories.map((repo: GitHubRepository) => {
              const isConnected = connectedRepoFullNames.includes(repo.full_name);
              const isConnecting = connectingFullName === repo.full_name;

              return (
                <div 
                  key={repo.full_name}
                  className="flex items-center justify-between p-4 bg-gray-800/50 border border-gray-700 rounded-xl hover:bg-gray-800 transition-colors"
                >
                  <div>
                    <h4 className="font-medium text-white flex items-center space-x-2">
                      <span>{repo.repo_name}</span>
                      {repo.private && (
                        <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded-full">Private</span>
                      )}
                    </h4>
                    <p className="text-sm text-gray-400 mt-1">{repo.full_name}</p>
                  </div>
                  
                  <button
                    onClick={() => handleConnect(repo)}
                    disabled={isConnected || isConnecting}
                    className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg font-medium text-sm transition-colors ${
                      isConnected
                        ? 'bg-green-500/10 text-green-500 cursor-default border border-green-500/20'
                        : isConnecting
                        ? 'bg-blue-600/50 text-white cursor-wait'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {isConnected ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Connected</span>
                      </>
                    ) : isConnecting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Connecting...</span>
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4" />
                        <span>Connect</span>
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}
        
        <div className="flex justify-between items-center pt-4 border-t border-gray-800">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white disabled:opacity-50 transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={githubRepositories.length < 30 || isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white disabled:opacity-50 transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </Modal>
  );
};
