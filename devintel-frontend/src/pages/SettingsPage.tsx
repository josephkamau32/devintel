import { useAuthStore } from '../store/authStore';
import { useLogout } from '../hooks/useAuth';
import { useCurrentUser } from '../hooks/useCurrentUser';
import { LogOut, ExternalLink } from 'lucide-react';

export function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { data: currentUser } = useCurrentUser();

  const displayUser = currentUser || user;

  return (
    <div className="space-y-6 max-w-2xl animate-fade-in">
      <div>
        <h1 className="text-h2 text-text-primary mb-1">Settings</h1>
        <p className="text-body text-text-tertiary">Manage your account and preferences.</p>
      </div>

      {/* Profile */}
      <div className="card">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Profile</h3>
        </div>
        <div className="p-5">
          <div className="flex items-center gap-4 mb-6">
            {displayUser?.avatar_url ? (
              <img src={displayUser.avatar_url} alt="" className="h-14 w-14 rounded-full" />
            ) : (
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-xl font-bold text-white">
                {(displayUser?.full_name?.[0] ?? displayUser?.email?.[0] ?? 'U').toUpperCase()}
              </div>
            )}
            <div>
              <p className="text-sm font-semibold text-text-primary">
                {displayUser?.full_name ?? displayUser?.github_username ?? 'User'}
              </p>
              <p className="text-xs text-text-tertiary">{displayUser?.email}</p>
              {displayUser?.github_username && (
                <a
                  href={`https://github.com/${displayUser.github_username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 mt-1 transition-colors"
                >
                  @{displayUser.github_username}
                  <ExternalLink className="h-2.5 w-2.5" />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Account */}
      <div className="card">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Account</h3>
        </div>
        <div className="p-5">
          <button
            onClick={() => logout.mutate()}
            className="flex items-center gap-2 bg-surface-3 hover:bg-surface-4 border border-border text-text-primary px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
