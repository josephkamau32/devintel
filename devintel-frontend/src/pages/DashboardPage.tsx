import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useLogout } from '../hooks/useAuth';
import { Button } from '../components/ui/button';
import { Plus, FolderGit2, Loader2, Github } from 'lucide-react';
import { useRepositories, indexRepository } from '../hooks/useRepositories';
import { RepositoryCard } from '../components/RepositoryCard';
import { ConnectRepoModal } from '../components/ConnectRepoModal';
import { Repository } from '../types/repository';

export const DashboardPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { repositories, isLoading, mutate } = useRepositories();
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);

  const handleIndex = async (id: string) => {
    try {
      await indexRepository(id);
      mutate();
    } catch (err) {
      console.error('Failed to start indexing:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-slate-800 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <span className="font-semibold text-xl">DevIntel AI</span>
          </div>

          <div className="flex items-center gap-4">
            {user?.avatar_url && (
              <img
                src={user.avatar_url}
                alt="avatar"
                className="h-8 w-8 rounded-full border border-slate-700"
              />
            )}
            <span className="text-sm text-slate-400">
              {user?.full_name ?? user?.email ?? user?.github_username}
            </span>
            <Button variant="ghost" onClick={() => logout.mutate()}>
              Sign out
            </Button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}!</h1>
            <p className="text-slate-400">Manage your connected repositories and workspaces.</p>
          </div>
          <button 
            onClick={() => setIsConnectModalOpen(true)}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20"
          >
            <Plus size={20} />
            <span>Connect Repository</span>
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center p-20">
            <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
          </div>
        ) : repositories.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-16 text-center shadow-sm">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-slate-800 mb-6 shadow-inner">
              <FolderGit2 className="w-10 h-10 text-blue-500" />
            </div>
            <h2 className="text-2xl font-semibold text-white mb-3">No repositories connected</h2>
            <p className="text-slate-400 max-w-md mx-auto mb-8 text-lg">
              Connect your first GitHub repository to start analyzing your codebase and chatting with DevIntel AI.
            </p>
            <button 
              onClick={() => setIsConnectModalOpen(true)}
              className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-colors shadow-lg shadow-blue-500/20"
            >
              <Github size={20} />
              <span>Connect GitHub Repository</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
            {repositories.map((repo: Repository) => (
              <RepositoryCard 
                key={repo.id} 
                repository={repo} 
                onIndex={handleIndex} 
              />
            ))}
          </div>
        )}

        <ConnectRepoModal 
          isOpen={isConnectModalOpen}
          onClose={() => setIsConnectModalOpen(false)}
          onConnect={() => {
            setIsConnectModalOpen(false);
            mutate();
          }}
          connectedRepoFullNames={repositories.map((r: Repository) => r.full_name)}
        />
      </main>
    </div>
  );
};
