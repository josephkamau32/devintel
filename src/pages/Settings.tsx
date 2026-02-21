import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { User, Key, CreditCard, Moon, Sun, Save } from "lucide-react";
import { getCurrentUser, type AuthUser } from "@/lib/auth";
import { toast } from "sonner";

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(getCurrentUser());
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");

  useEffect(() => {
    const handleUserUpdate = () => {
      const u = getCurrentUser();
      setUser(u);
      setName(u?.name || "");
      setEmail(u?.email || "");
    };
    window.addEventListener('user-updated', handleUserUpdate);
    return () => window.removeEventListener('user-updated', handleUserUpdate);
  }, []);

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  const handleSaveProfile = () => {
    // Update localStorage user data
    if (user) {
      const updatedUser = { ...user, name, email };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      window.dispatchEvent(new CustomEvent('user-updated', { detail: updatedUser }));
      toast.success("Profile updated successfully");
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <User className="h-4 w-4 text-muted-foreground" />
          <h2 className="font-semibold text-card-foreground">Profile</h2>
        </div>
        <div className="space-y-4">
          {/* Avatar */}
          {user?.avatar_url && (
            <div className="flex items-center gap-4">
              <img
                src={user.avatar_url}
                alt={name || "Profile"}
                className="h-16 w-16 rounded-full object-cover border-2 border-border"
              />
              <div>
                <p className="text-sm font-medium text-foreground">{name || 'No name set'}</p>
                <p className="text-xs text-muted-foreground">GitHub ID: {user.github_id}</p>
              </div>
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium text-foreground">Full name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>
          <Button size="sm" className="gap-2" onClick={handleSaveProfile}>
            <Save className="h-3 w-3" />
            Save Changes
          </Button>
        </div>
      </div>

      {/* Connected Account */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Key className="h-4 w-4 text-muted-foreground" />
          <h2 className="font-semibold text-card-foreground">Connected Account</h2>
        </div>
        <div className="flex items-center gap-3 p-3 rounded-lg bg-accent">
          <svg className="h-5 w-5 text-foreground" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">GitHub</p>
            <p className="text-xs text-muted-foreground">Connected as {user?.name || user?.github_id || 'Unknown'}</p>
          </div>
          <span className="text-xs font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">Connected</span>
        </div>
      </div>

      {/* Billing */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard className="h-4 w-4 text-muted-foreground" />
          <h2 className="font-semibold text-card-foreground">Billing</h2>
        </div>
        <p className="text-sm text-muted-foreground">You are on the <span className="font-medium text-foreground">Free Plan</span>.</p>
        <Button className="mt-3" size="sm">Upgrade to Pro — $29/mo</Button>
      </div>

      {/* Theme */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {darkMode ? <Moon className="h-4 w-4 text-muted-foreground" /> : <Sun className="h-4 w-4 text-muted-foreground" />}
            <h2 className="font-semibold text-card-foreground">Appearance</h2>
          </div>
          <button
            onClick={toggleTheme}
            className="relative h-6 w-11 rounded-full bg-muted transition-colors"
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-primary transition-transform ${darkMode ? "left-[22px]" : "left-0.5"
                }`}
            />
          </button>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          {darkMode ? "Dark mode is enabled" : "Light mode is enabled"}
        </p>
      </div>
    </div>
  );
}
