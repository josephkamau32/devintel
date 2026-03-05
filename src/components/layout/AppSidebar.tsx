import { useState, useEffect } from "react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  GitBranch,
  MessageSquare,
  GitPullRequest,
  BarChart3,
  Shield,
  Settings,
  ChevronLeft,
  Zap,
  X,
} from "lucide-react";
import { getCurrentUser, type AuthUser } from "@/lib/auth";

const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "My Repositories", url: "/repositories", icon: GitBranch },
  { title: "AI Chat", url: "/chat", icon: MessageSquare },
  { title: "Pull Requests", url: "/pull-requests", icon: GitPullRequest },
  { title: "Code Health", url: "/code-health", icon: Shield },
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "Settings", url: "/settings", icon: Settings },
];

interface AppSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({ mobileOpen, onMobileClose }: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(getCurrentUser());
  const location = useLocation();
  const [tooltip, setTooltip] = useState<string | null>(null);

  useEffect(() => {
    const handleUserUpdate = () => setUser(getCurrentUser());
    window.addEventListener("user-updated", handleUserUpdate);
    return () => window.removeEventListener("user-updated", handleUserUpdate);
  }, []);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    onMobileClose();
  }, [location.pathname]);

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
          <Zap className="h-4 w-4 text-primary-foreground" />
        </div>
        {!collapsed && (
          <span className="text-sm font-semibold text-foreground">DevIntel AI</span>
        )}
        <button
          onClick={() => {
            if (window.innerWidth < 768) {
              onMobileClose();
            } else {
              setCollapsed(!collapsed);
            }
          }}
          className="ml-auto flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <span className="md:hidden"><X className="h-4 w-4" /></span>
          <span className="hidden md:block">
            <ChevronLeft className={`h-4 w-4 transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`} />
          </span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 p-2">
        {navItems.map((item) => (
          <div
            key={item.url}
            className="relative"
            onMouseEnter={() => collapsed && setTooltip(item.title)}
            onMouseLeave={() => setTooltip(null)}
          >
            <NavLink
              to={item.url}
              end
              className={`flex items-center rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground ${collapsed ? "justify-center gap-0" : "gap-3"}`}
              activeClassName="bg-accent text-foreground font-medium"
              onClick={onMobileClose}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.title}</span>}
            </NavLink>

            {/* Tooltip when collapsed */}
            <AnimatePresence>
              {collapsed && tooltip === item.title && (
                <motion.div
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -4 }}
                  transition={{ duration: 0.12 }}
                  className="absolute left-full top-1/2 -translate-y-1/2 ml-2 z-50 whitespace-nowrap rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium text-card-foreground shadow-md pointer-events-none"
                >
                  {item.title}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </nav>

      {/* Bottom — User info */}
      {!collapsed && (
        <div className="border-t border-border p-4">
          <div className="rounded-lg bg-accent p-3">
            <p className="text-xs font-medium text-foreground">Free Plan</p>
            <p className="mt-1 text-xs text-muted-foreground truncate">
              {user?.name ? `Signed in as ${user.name}` : "Welcome to DevIntel AI"}
            </p>
            <button className="mt-2 text-xs font-medium text-primary hover:underline">
              Upgrade to Pro
            </button>
          </div>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile backdrop */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
            onClick={onMobileClose}
          />
        )}
      </AnimatePresence>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.aside
            initial={{ x: -240 }}
            animate={{ x: 0 }}
            exit={{ x: -240 }}
            transition={{ type: "spring", stiffness: 320, damping: 30 }}
            className="fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-sidebar md:hidden"
          >
            <SidebarContent />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex flex-col border-r border-border bg-sidebar transition-all duration-200 ${collapsed ? "w-16" : "w-60"
          }`}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
