import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useLogout } from '../hooks/useAuth';
import { LogOut, Code2, ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export function Navbar() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-40 border-b border-border bg-surface-0/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Left: Logo + nav links */}
        <div className="flex items-center gap-6">
          <Link to="/dashboard" className="flex items-center gap-2.5 group">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600">
              <Code2 className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-text-primary tracking-tight">
              DevIntel
            </span>
          </Link>

          <div className="hidden sm:flex items-center gap-1">
            <Link
              to="/dashboard"
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                isActive('/dashboard')
                  ? 'text-text-primary bg-surface-3'
                  : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-3'
              }`}
            >
              Repositories
            </Link>
          </div>
        </div>

        {/* Right: User menu */}
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
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="h-6 w-6 rounded-full"
                  />
                ) : (
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-[10px] font-semibold text-white">
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
      </div>
    </nav>
  );
}
