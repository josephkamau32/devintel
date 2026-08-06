import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { Navbar } from '../components/Navbar';
import { Plus, FolderGit2, Github } from 'lucide-react';
import { useRepositories, indexRepository } from '../hooks/useRepositories';
import { RepositoryCard } from '../components/RepositoryCard';
import { ConnectRepoModal } from '../components/ConnectRepoModal';
import { Repository } from '../types/repository';
import toast from 'react-hot-toast';

/** Skeleton card shown while repositories are loading */
function RepositoryCardSkeleton() {
  return (
    <div className="card p-5">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg skeleton" />
          <div>
            <div className="h-4 w-28 rounded skeleton mb-1.5" />
            <div className="h-3 w-20 rounded skeleton" />
          </div>
        </div>
        <div className="h-5 w-16 rounded-md skeleton" />
      </div>
      <div className="h-3 w-full rounded skeleton mb-1.5" />
      <div className="h-3 w-3/4 rounded skeleton mb-4" />
      <div className="flex items-center justify-between pt-3 border-t border-border">
        <div className="flex gap-3">
          <div className="h-3 w-14 rounded skeleton" />
          <div className="h-3 w-10 rounded skeleton" />
        </div>
        <div className="h-7 w-20 rounded-md skeleton" />
      </div>
    </div>
  );
}

export const DashboardPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
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
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 sm:px-6 py-8">
        {/* Welcome header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div className="animate-fade-in">
            <h1 className="text-h2 text-text-primary mb-1">
              {greeting}{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
            </h1>
            <p className="text-body text-text-tertiary">
              {repositories.length > 0
                ? `You have ${repositories.length} connected repositor${repositories.length === 1 ? 'y' : 'ies'}.`
                : 'Connect your first repository to get started.'}
            </p>
          </div>
          <button 
            onClick={() => setIsConnectModalOpen(true)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-subtle hover:shadow-medium"
          >
            <Plus className="h-4 w-4" />
            <span>Connect Repository</span>
          </button>
        </div>

        {/* Repository grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <RepositoryCardSkeleton key={i} />
            ))}
          </div>
        ) : repositories.length === 0 ? (
          <div className="card p-14 text-center animate-fade-in">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-surface-3 mb-5 border border-border">
              <FolderGit2 className="w-7 h-7 text-text-quaternary" />
            </div>
            <h2 className="text-h3 text-text-primary mb-2">No repositories connected</h2>
            <p className="text-body text-text-tertiary max-w-sm mx-auto mb-7">
              Connect your first GitHub repository to start analyzing your codebase and chatting with DevIntel AI.
            </p>
            <button 
              onClick={() => setIsConnectModalOpen(true)}
              className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-all shadow-subtle hover:shadow-medium"
            >
              <Github className="h-4 w-4" />
              <span>Connect GitHub Repository</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
            {repositories.map((repo: Repository, index: number) => (
              <div
                key={repo.id}
                className="animate-slide-up"
                style={{ animationDelay: `${index * 40}ms` }}
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
