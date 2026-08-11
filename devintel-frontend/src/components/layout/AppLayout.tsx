import { useState, useCallback, lazy, Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { useRepositories } from '../../hooks/useRepositories';
import { clsx } from 'clsx';

const GlobalSearch = lazy(() =>
  import('../GlobalSearch').then((m) => ({ default: m.GlobalSearch })),
);

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const { repositories } = useRepositories();

  const handleSearchOpen = useCallback(() => setSearchOpen(true), []);
  const handleSearchClose = useCallback(() => setSearchOpen(false), []);

  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      {/* Sidebar — hidden on mobile, visible on sm+ */}
      <div className="hidden md:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          repoCount={repositories.length}
        />
      </div>

      {/* Main content area */}
      <div
        className={clsx(
          'transition-all duration-200',
          sidebarCollapsed ? 'md:ml-[64px]' : 'md:ml-[240px]',
        )}
      >
        <TopBar onSearchOpen={handleSearchOpen} />
        <main className="mx-auto max-w-[1400px] px-4 sm:px-6 py-6">
          <Outlet />
        </main>
      </div>

      {/* Global Search Modal */}
      <Suspense fallback={null}>
        {searchOpen && <GlobalSearch onClose={handleSearchClose} repositories={repositories} />}
      </Suspense>
    </div>
  );
}
