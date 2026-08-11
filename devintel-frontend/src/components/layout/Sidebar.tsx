import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  Sparkles,
  Network,
  Shield,
  Gauge,
  MessageSquareText,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Code2,
} from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  repoCount?: number;
}

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/repositories', icon: FolderGit2, label: 'Repositories', badge: true },
  { to: '/insights', icon: Sparkles, label: 'AI Insights' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
];

const workspaceItems = [
  { to: '/architecture', icon: Network, label: 'Architecture' },
  { to: '/security', icon: Shield, label: 'Security' },
  { to: '/performance', icon: Gauge, label: 'Performance' },
  { to: '/reviews', icon: MessageSquareText, label: 'Reviews' },
];

export function Sidebar({ collapsed, onToggle, repoCount }: SidebarProps) {
  const location = useLocation();

  // Check if we're in a repo workspace
  const repoMatch = location.pathname.match(/^\/repositories\/([^/]+)/);
  const inWorkspace = !!repoMatch;

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 z-30 h-screen flex flex-col border-r border-border bg-surface-1 transition-all duration-200',
        collapsed ? 'w-[64px]' : 'w-[240px]',
      )}
    >
      {/* Logo */}
      <div className={clsx('flex items-center h-14 border-b border-border', collapsed ? 'justify-center px-0' : 'px-4')}>
        <NavLink to="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 flex-shrink-0">
            <Code2 className="h-4 w-4 text-white" />
          </div>
          {!collapsed && (
            <span className="text-sm font-bold text-text-primary tracking-tight">DevIntel</span>
          )}
        </NavLink>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1 no-scrollbar">
        {!collapsed && (
          <div className="px-3 mb-2 text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
            Platform
          </div>
        )}
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  'sidebar-nav-item',
                  isActive && 'sidebar-nav-item-active',
                  collapsed && 'justify-center px-0',
                )
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="h-[18px] w-[18px] flex-shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
              {!collapsed && item.badge && repoCount !== undefined && repoCount > 0 && (
                <span className="ml-auto text-[10px] font-semibold bg-surface-4 text-text-tertiary px-1.5 py-0.5 rounded-md">
                  {repoCount}
                </span>
              )}
            </NavLink>
          );
        })}

        {inWorkspace && (
          <>
            {!collapsed && (
              <div className="px-3 mt-5 mb-2 text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
                Workspace
              </div>
            )}
            {collapsed && <div className="border-t border-border my-2" />}
            {workspaceItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={`/repositories/${repoMatch![1]}${item.to === '/architecture' ? '/architecture' : item.to === '/security' ? '/health' : item.to === '/performance' ? '/health' : '/reviews'}`}
                  className={({ isActive }) =>
                    clsx(
                      'sidebar-nav-item',
                      isActive && 'sidebar-nav-item-active',
                      collapsed && 'justify-center px-0',
                    )
                  }
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="h-[18px] w-[18px] flex-shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              );
            })}
          </>
        )}

        {!collapsed && (
          <>
            <div className="border-t border-border my-3" />
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                clsx('sidebar-nav-item', isActive && 'sidebar-nav-item-active')
              }
            >
              <Settings className="h-[18px] w-[18px] flex-shrink-0" />
              <span className="truncate">Settings</span>
            </NavLink>
          </>
        )}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border p-2">
        <button
          onClick={onToggle}
          className="sidebar-nav-item w-full justify-center"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
