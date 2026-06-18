import { useAuthStore } from '../store/authStore';
import { useLogout } from '../hooks/useAuth';
import { Button } from '../components/ui/button';

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-slate-800 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <span className="font-semibold">DevIntel AI</span>
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

      <main className="mx-auto max-w-6xl px-6 py-12">
        <h1 className="text-3xl font-bold">
          Welcome{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}!
        </h1>
        <p className="mt-2 text-slate-400">
          Connect a GitHub repository to start chatting with your codebase.
        </p>

        <div className="mt-10 rounded-xl border border-dashed border-slate-700 p-12 text-center">
          <svg className="mx-auto mb-4 h-12 w-12 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M12 4v16m8-8H4" />
          </svg>
          <p className="text-sm text-slate-400">Connect your first repository to get started</p>
          <Button className="mt-4">Connect Repository</Button>
        </div>
      </main>
    </div>
  );
}
