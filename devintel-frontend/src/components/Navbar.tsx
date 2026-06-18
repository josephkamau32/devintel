import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export function Navbar() {
  const user = useAuthStore((s) => s.user);

  return (
    <nav className="border-b border-slate-800 px-6 py-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <Link to="/" className="font-semibold text-white">
          DevIntel AI
        </Link>
        <div className="flex items-center gap-4 text-sm text-slate-300">
          {user?.email ?? user?.github_username}
          <Link to="/dashboard" className="text-violet-400 hover:text-violet-300">
            Dashboard
          </Link>
        </div>
      </div>
    </nav>
  );
}
