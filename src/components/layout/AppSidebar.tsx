import { useState } from "react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  GitBranch,
  MessageSquare,
  GitPullRequest,
  BarChart3,
  Settings,
  ChevronLeft,
  Zap,
} from "lucide-react";

const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "My Repositories", url: "/repositories", icon: GitBranch },
  { title: "AI Chat", url: "/chat", icon: MessageSquare },
  { title: "Pull Requests", url: "/pull-requests", icon: GitPullRequest },
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "Settings", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={`flex flex-col border-r border-border bg-sidebar transition-all duration-200 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
          <Zap className="h-4 w-4 text-primary-foreground" />
        </div>
        {!collapsed && (
          <span className="text-sm font-semibold text-foreground">DevIntel AI</span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <ChevronLeft
            className={`h-4 w-4 transition-transform ${collapsed ? "rotate-180" : ""}`}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => (
          <NavLink
            key={item.url}
            to={item.url}
            end
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            activeClassName="bg-accent text-foreground font-medium"
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && <span>{item.title}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      {!collapsed && (
        <div className="border-t border-border p-4">
          <div className="rounded-lg bg-accent p-3">
            <p className="text-xs font-medium text-foreground">Free Plan</p>
            <p className="mt-1 text-xs text-muted-foreground">48/50 AI queries used</p>
            <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
              <div className="h-1.5 rounded-full bg-primary" style={{ width: "96%" }} />
            </div>
            <button className="mt-2 text-xs font-medium text-primary hover:underline">
              Upgrade to Pro
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
