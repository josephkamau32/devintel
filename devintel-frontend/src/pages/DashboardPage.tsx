import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useLogout } from '../hooks/useAuth';
import { Button } from '../components/ui/button';
import { Plus, FolderGit2, Github } from 'lucide-react';
import { useRepositories, indexRepository } from '../hooks/useRepositories';
import { RepositoryCard } from '../components/RepositoryCard';
import { ConnectRepoModal } from '../components/ConnectRepoModal';
import { Repository } from '../types/repository';
import toast from 'react-hot-toast';

/** Skeleton card shown while repositories are loading */
function RepositoryCardSkeleton() {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 animate-pulse">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-slate-800" />
          <div>
            <div className="h-4 w-32 bg-slate-800 rounded mb-2" />
            <div className="h-3 w-24 bg-slate-800/60 rounded" />
          </div>
        </div>
        <div className="h-5 w-20 bg-slate-800 rounded" />
      </div>
      <div className="h-3 w-full bg-slate-800/40 rounded mb-2" />
      <div className="h-3 w-3/4 bg-slate-800/40 rounded mb-4" />
      <div className="flex items-center justify-between mt-4">
        <div className="flex space-x-4">
          <div className="h-3 w-16 bg-slate-800/40 rounded" />
          <div className="h-3 w-12 bg-slate-800/40 rounded" />
        </div>
        <div className="h-9 w-24 bg-slate-800 rounded-lg" />
      </div>
    </div>
  );
}

export const DashboardPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { repositories, isLoading, mutate } = useRepositories();
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);
  const [indexingIds, setIndexingIds] = useState<Set<string>>(new Set());

  const handleIndex = async (id: string) => {
    setIndexingIds((prev) => new Set(prev).add(id));
    try {
      await indexRepository(id);
      toast.success('Indexing started! This may take a moment.');
      mutate();
    } catch (err) {
      toast.error('Failed to start indexing. Please try again.');
      console.error('Failed to start indexing:', err);
    } finally {
      setIndexingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  })();

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Subtle background glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-1/2 right-0 h-[600px] w-[600px] rounded-full bg-violet-600/5 blur-[120px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-slate-800/50 backdrop-blur-md bg-slate-950/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 shadow-lg shadow-violet-500/20">
              <svg className="h-4.5 w-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <span className="font-bold text-xl tracking-tight">DevIntel AI</span>
          </div>

          <div className="flex items-center gap-4">
            {user?.avatar_url && (
              <img
                src={user.avatar_url}
                alt="avatar"
                className="h-8 w-8 rounded-full border-2 border-slate-700 ring-2 ring-slate-800"
              />
            )}
            <span className="hidden sm:block text-sm text-slate-400">
              {user?.full_name ?? user?.email ?? user?.github_username}
            </span>
            <Button variant="ghost" onClick={() => logout.mutate()}>
              Sign out
            </Button>
          </div>
        </div>
      </nav>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-4">
          <div className="animate-fade-in">
            <h1 className="text-3xl font-bold text-white mb-1.5">
              {greeting}{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}! 👋
            </h1>
            <p className="text-slate-400">
              {repositories.length > 0
                ? `You have ${repositories.length} connected repositor${repositories.length === 1 ? 'y' : 'ies'}.`
                : 'Connect your first repository to get started.'}
            </p>
          </div>
          <button 
            onClick={() => setIsConnectModalOpen(true)}
            className="flex items-center space-x-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:brightness-110 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-violet-500/20 hover:shadow-xl hover:shadow-violet-500/30 hover:scale-[1.02]"
          >
            <Plus size={18} />
            <span>Connect Repository</span>
          </button>
        </div>

        {/* Repository grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[...Array(6)].map((_, i) => (
              <RepositoryCardSkeleton key={i} />
            ))}
          </div>
        ) : repositories.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-16 text-center animate-fade-in">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-slate-800/80 mb-6 border border-slate-700">
              <FolderGit2 className="w-10 h-10 text-violet-400" />
            </div>
            <h2 className="text-2xl font-semibold text-white mb-3">No repositories connected</h2>
            <p className="text-slate-400 max-w-md mx-auto mb-8 text-base">
              Connect your first GitHub repository to start analyzing your codebase and chatting with DevIntel AI.
            </p>
            <button 
              onClick={() => setIsConnectModalOpen(true)}
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:brightness-110 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg shadow-violet-500/20 hover:shadow-xl hover:shadow-violet-500/30"
            >
              <Github size={18} />
              <span>Connect GitHub Repository</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-fade-in">
            {repositories.map((repo: Repository, index: number) => (
              <div
                key={repo.id}
                className="animate-slide-up"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <RepositoryCard 
                  repository={repo} 
                  onIndex={handleIndex}
                  isTriggering={indexingIds.has(repo.id)}
                />
              </div>
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
