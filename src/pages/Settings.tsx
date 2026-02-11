import { useState } from "react";
import { Button } from "@/components/ui/button";
import { User, Key, CreditCard, Moon, Sun } from "lucide-react";

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(true);

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
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
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium text-foreground">Full name</label>
              <input
                type="text"
                defaultValue="John Doe"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Email</label>
              <input
                type="email"
                defaultValue="john@company.com"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>
          <Button size="sm">Save Changes</Button>
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
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-primary transition-transform ${
                darkMode ? "left-[22px]" : "left-0.5"
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
