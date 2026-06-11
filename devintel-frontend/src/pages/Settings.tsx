import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Building2, CreditCard, Key, Loader2, Moon, Sun, User, Github } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import OrganizationsSettings from "./Settings/Organizations";

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');

  // Load user data from localStorage on mount
  useEffect(() => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        setUserName(user.name || user.login || '');
        setUserEmail(user.email || '');
      }
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Failed to load user data:', error);
      }
    }
  }, []);

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  const [isLoading, setIsLoading] = useState(false);

  const handleSaveProfile = async () => {
    setIsLoading(true);
    // Save to localStorage and Backend
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        user.name = userName;
        user.email = userEmail;

        // 1. Update Backend
        await apiClient.put('/api/v1/auth/me', { name: userName, email: userEmail });

        // 2. Update Local Storage
        localStorage.setItem('user', JSON.stringify(user));

        // 3. Notify other components
        window.dispatchEvent(new CustomEvent('user-updated', { detail: user }));

        toast.success('Profile updated successfully!');
      } else {
        toast.error('No user data found. Please log in again.');
      }
    } catch (error) {
      console.error('Failed to save user data:', error);
      toast.error('Failed to save profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGitHubConnect = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<{ url: string }>("/api/v1/auth/github");
      window.location.href = response.url;
    } catch (error) {
      toast.error("Failed to connect to GitHub. Please try again.");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your account and preferences</p>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="mb-6 grid w-full grid-cols-2 md:w-[400px]">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="organizations">Organizations</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6 mt-0">
          {/* Profile */}
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="h-4 w-4 text-muted-foreground" />
              <h2 className="font-semibold text-card-foreground">Profile</h2>
            </div>
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-foreground">Full name</label>
                  <input
                    type="text"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    placeholder="Your name"
                    className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground">Email</label>
                  <input
                    type="email"
                    value={userEmail}
                    onChange={(e) => setUserEmail(e.target.value)}
                    placeholder="your.email@example.com"
                    className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>
              <Button size="sm" onClick={handleSaveProfile} disabled={isLoading}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save Changes
              </Button>
            </div>
          </div>

          {/* Linked Accounts */}
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Github className="h-4 w-4 text-muted-foreground" />
              <h2 className="font-semibold text-card-foreground">Linked Accounts</h2>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">GitHub</p>
                <p className="text-sm text-muted-foreground">
                  {JSON.parse(localStorage.getItem('user') || '{}')?.github_id 
                    ? "Your GitHub account is connected." 
                    : "Connect GitHub to access repository analysis features."}
                </p>
              </div>
              {!JSON.parse(localStorage.getItem('user') || '{}')?.github_id && (
                <Button variant="outline" size="sm" onClick={handleGitHubConnect}>
                  Connect
                </Button>
              )}
            </div>
          </div>

          {/* API Usage */}
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Key className="h-4 w-4 text-muted-foreground" />
              <h2 className="font-semibold text-card-foreground">API Usage</h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">AI Queries</span>
                <span className="text-foreground">48 / 50</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div className="h-2 rounded-full bg-primary" style={{ width: "96%" }} />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Repositories</span>
                <span className="text-foreground">5 / 3</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div className="h-2 rounded-full bg-warning" style={{ width: "100%" }} />
              </div>
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
        </TabsContent>

        <TabsContent value="organizations" className="mt-0">
          <OrganizationsSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
