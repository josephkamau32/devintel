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
  X,
  Search,
  Building2,
  User,
} from "lucide-react";
import { toast } from "sonner";
import { useOrganization } from "@/contexts/OrganizationContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
} from "@/components/ui/select";

const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "My Repositories", url: "/repositories", icon: GitBranch },
  { title: "AI Chat", url: "/chat", icon: MessageSquare },
  { title: "Semantic Search", url: "/search", icon: Search },
  { title: "Pull Requests", url: "/pull-requests", icon: GitPullRequest },
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "Settings", url: "/settings", icon: Settings },
];

interface AppSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({ mobileOpen, onMobileClose }: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { organizations, currentOrganization, setCurrentOrganizationId } = useOrganization();

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="flex h-14 items-center justify-between border-b border-border/30 px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/20 border border-primary/30 shadow-[0_0_15px_-3px_hsl(var(--primary)/0.3)]">
            <Zap className="h-4 w-4 text-primary animate-pulse-slow" />
          </div>
          {!collapsed && (
            <span className="text-sm font-bold tracking-wide text-foreground gradient-text">DevIntel AI</span>
          )}
        </div>

        {/* Close on mobile, collapse on desktop */}
        <button
          onClick={() => {
            if (window.innerWidth < 768) {
              onMobileClose();
            } else {
              setCollapsed(!collapsed);
            }
          }}
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <span className="md:hidden"><X className="h-4 w-4" /></span>
          <span className="hidden md:block">
            <ChevronLeft className={`h-4 w-4 transition-transform ${collapsed ? "rotate-180" : ""}`} />
          </span>
        </button>
      </div>

      {/* Organization Switcher */}
      {!collapsed && (
        <div className="p-4 border-b border-border">
          <Select
            value={currentOrganization?.id || "personal"}
            onValueChange={(value) => {
              setCurrentOrganizationId(value === "personal" ? null : value);
            }}
          >
            <SelectTrigger className="w-full h-9 bg-accent/50 border-0 focus:ring-1 focus:ring-primary/20">
              <SelectValue placeholder="Select Context" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="personal">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span>Personal</span>
                  </div>
                </SelectItem>
              </SelectGroup>

              {organizations.length > 0 && (
                <SelectGroup>
                  <SelectLabel className="text-xs font-medium text-muted-foreground flex items-center gap-2 mt-2 px-2">
                    <Building2 className="h-3 w-3" /> Organizations
                  </SelectLabel>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      <div className="flex items-center gap-2">
                        <div className="flex h-5 w-5 items-center justify-center rounded bg-primary/10 text-primary text-[10px] font-bold uppercase">
                          {org.name.substring(0, 2)}
                        </div>
                        <span className="truncate">{org.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectGroup>
              )}
            </SelectContent>
          </Select>
        </div>
      )}


      {/* Navigation */}
      <nav className="flex-1 space-y-1.5 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.url}
            to={item.url}
            end
            className="group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground transition-all duration-300 hover:bg-white/5 hover:text-foreground hover:translate-x-1"
            activeClassName="bg-gradient-to-r from-primary/20 to-transparent text-primary font-medium border-l-2 border-primary relative shadow-[inset_0_0_20px_-5px_hsl(var(--primary)/0.15)]"
            onClick={onMobileClose}
          >
            <item.icon className="h-4 w-4 shrink-0 transition-transform duration-300 group-hover:scale-110 group-active:scale-95" />
            {(!collapsed || mobileOpen) && <span>{item.title}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      {(!collapsed || mobileOpen) && (
        <div className="border-t border-border p-4">
          <div className="rounded-lg bg-accent p-3">
            <p className="text-xs font-medium text-foreground">Free Plan</p>
            <p className="mt-1 text-xs text-muted-foreground">48/50 AI queries used</p>
            <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
              <div className="h-1.5 rounded-full bg-primary" style={{ width: "96%" }} />
            </div>
            <button
              onClick={() => toast.info("Pro tier coming soon!")}
              className="mt-2 text-xs font-medium text-primary hover:underline"
            >
              Upgrade to Pro
            </button>
          </div>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onMobileClose}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border/30 bg-background/60 backdrop-blur-2xl transition-transform duration-300 md:hidden ${mobileOpen ? "translate-x-0" : "-translate-x-full"
          }`}
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex flex-col border-r border-border/30 bg-background/40 backdrop-blur-xl transition-all duration-300 ${collapsed ? "w-16" : "w-60"
          }`}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
