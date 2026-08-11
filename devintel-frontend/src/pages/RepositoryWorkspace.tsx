import { NavLink, Outlet, useParams, useNavigate } from 'react-router-dom';
import { useRepository } from '../hooks/useAPI';
import { Code2, LayoutDashboard, Network, MessageSquareText, Activity, GitPullRequest, GitBranch, History, Settings, ArrowLeft, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

const tabs = [
  { to: '', icon: LayoutDashboard, label: 'Overview', end: true },
  { to: 'architecture', icon: Network, label: 'Architecture' },
  { to: 'chat', icon: MessageSquareText, label: 'AI Chat' },
  { to: 'health', icon: Activity, label: 'Health' },
  { to: 'reviews', icon: GitPullRequest, label: 'Reviews' },
  { to: 'pulls', icon: GitBranch, label: 'Pull Requests' },
  { to: 'history', icon: History, label: 'Git History' },
  { to: 'settings', icon: Settings, label: 'Settings' },
];

export function RepositoryWorkspace() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: repository, isLoading } = useRepository(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 text-brand-400 animate-spin-slow" />
      </div>
    );
  }

  if (!repository) {
    return (
      <div className="card p-10 text-center">
        <p className="text-sm text-text-tertiary mb-4">Repository not found.</p>
        <button
          onClick={() => navigate('/repositories')}
          className="text-sm text-brand-400 hover:text-brand-300 transition-colors"
        >
          ← Back to repositories
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-0 animate-fade-in">
      {/* Workspace header */}
      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={() => navigate('/repositories')}
          className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-surface-3 transition-colors text-text-tertiary hover:text-text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface-4 text-text-tertiary">
            <Code2 className="w-[18px] h-[18px]" />
          </div>
          <div>
            <h1 className="text-h4 text-text-primary">{repository.repo_name}</h1>
            <p className="text-xs text-text-quaternary">{repository.full_name}</p>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="border-b border-border mb-6 -mx-4 sm:-mx-6 px-4 sm:px-6">
        <nav className="flex gap-0 overflow-x-auto no-scrollbar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  clsx('workspace-tab flex items-center gap-2 whitespace-nowrap', isActive && 'workspace-tab-active')
                }
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Tab content */}
      <Outlet context={{ repository }} />
    </div>
  );
}
