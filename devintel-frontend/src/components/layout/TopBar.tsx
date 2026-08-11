import { useState, useRef, useEffect, useCallback } from 'react';
import { useAuthStore } from '../../store/authStore';
import { useLogout } from '../../hooks/useAuth';
import { LogOut, Search, ChevronDown, Command } from 'lucide-react';

interface TopBarProps {
  onSearchOpen: () => void;
}

export function TopBar({ onSearchOpen }: TopBarProps) {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  // Global keyboard shortcut
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onSearchOpen();
      }
    },
    [onSearchOpen],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-surface-0/80 backdrop-blur-md px-6">
      {/* Search trigger */}
      <button
        onClick={onSearchOpen}
        className="flex items-center gap-3 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-quaternary hover:text-text-tertiary hover:border-border-medium transition-all max-w-xs w-64"
      >
        <Search className="h-3.5 w-3.5 flex-shrink-0" />
        <span className="flex-1 text-left truncate">Search everything…</span>
        <kbd className="hidden sm:flex items-center gap-0.5 text-[10px] text-text-quaternary bg-surface-4 px-1.5 py-0.5 rounded font-medium border border-border">
          <Command className="h-2.5 w-2.5" />K
        </kbd>
      </button>

      {/* User menu */}
      <div className="flex items-center gap-3">
        {user && (
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-surface-3"
              aria-expanded={menuOpen}
              aria-haspopup="true"
            >
              {user.avatar_url ? (
                <img src={user.avatar_url} alt="" className="h-7 w-7 rounded-full" />
              ) : (
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-[11px] font-semibold text-white">
                  {(user.full_name?.[0] ?? user.email?.[0] ?? 'U').toUpperCase()}
                </div>
              )}
              <span className="hidden sm:block text-sm text-text-secondary max-w-[120px] truncate">
                {user.full_name ?? user.github_username ?? user.email}
              </span>
              <ChevronDown className="h-3.5 w-3.5 text-text-quaternary" />
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-1.5 w-52 rounded-lg border border-border bg-surface-1 shadow-elevated animate-scale-in origin-top-right">
                <div className="px-3 py-2.5 border-b border-border">
                  <p className="text-sm font-medium text-text-primary truncate">
                    {user.full_name ?? user.github_username ?? 'User'}
                  </p>
                  <p className="text-xs text-text-tertiary truncate">
                    {user.email ?? user.github_username}
                  </p>
                </div>
                <div className="p-1">
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      logout.mutate();
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
