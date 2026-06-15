import { Search, Bell, ChevronDown, User, Menu, LogOut, Settings, User as UserIcon, Trash2 } from "lucide-react";
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

interface AppHeaderProps {
  onMenuClick: () => void;
}

interface Notification {
  id: string;
  title: string;
  description: string;
  time: string;
  read: boolean;
}

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    title: 'New Analysis Complete',
    description: 'Repository "devintel-backend" analysis finished successfully.',
    time: '2m ago',
    read: false,
  },
  {
    id: '2',
    title: 'Security Alert',
    description: 'Potential vulnerability detected in dependencies.',
    time: '1h ago',
    read: false,
  },
  {
    id: '3',
    title: 'Welcome to DevIntel',
    description: 'Get started by connecting your first repository.',
    time: '1d ago',
    read: true,
  }
];

import { useAuth } from "../../contexts/AuthContext";

export function AppHeader({ onMenuClick }: AppHeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchFocused, setSearchFocused] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(MOCK_NOTIFICATIONS);
  const unreadCount = notifications.filter(n => !n.read).length;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };



  return (
    <header className="flex h-14 items-center justify-between border-b border-border/30 bg-background/40 backdrop-blur-xl px-4 sm:px-6 sticky top-0 z-40">
      {/* Left: hamburger + search */}
      <div className="flex items-center gap-3 flex-1">
        <button
          onClick={onMenuClick}
          className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="relative w-full max-w-md group">
          <Search className={`absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transition-colors duration-300 ${searchFocused ? "text-primary" : "text-muted-foreground"}`} />
          <input
            type="text"
            placeholder="Search repositories, files, or ask AI..."
            className={`h-9 w-full rounded-full border bg-background/50 backdrop-blur-sm pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none transition-all duration-300 ${searchFocused ? "border-primary shadow-[0_0_15px_-3px_hsl(var(--primary)/0.4)]" : "border-border/50 hover:border-primary/50"
              }`}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground hidden sm:inline">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3 ml-3">
        {/* Notifications Popover */}
        <Popover>
          <PopoverTrigger asChild>
            <button className="relative flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary ring-2 ring-background" />
              )}
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-0" align="end">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/40">
              <h4 className="font-semibold text-sm">Notifications</h4>
              {notifications.length > 0 && (
                <button
                  onClick={clearAllNotifications}
                  className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
                >
                  <Trash2 className="h-3 w-3" />
                  Clear all
                </button>
              )}
            </div>
            <ScrollArea className="h-[300px]">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-6 text-center text-muted-foreground">
                  <Bell className="h-8 w-8 mb-2 opacity-20" />
                  <p className="text-sm">No new notifications</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-border">
                  {notifications.map((notification) => (
                    <button
                      key={notification.id}
                      onClick={() => markAsRead(notification.id)}
                      className={`flex flex-col items-start gap-1 p-4 text-left transition-colors hover:bg-accent/50 ${!notification.read ? 'bg-accent/10' : ''
                        }`}
                    >
                      <div className="flex items-start justify-between w-full">
                        <span className={`text-sm font-medium ${!notification.read ? 'text-foreground' : 'text-muted-foreground'}`}>
                          {notification.title}
                        </span>
                        <span className="text-[10px] text-muted-foreground whitespace-nowrap ml-2">{notification.time}</span>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                        {notification.description}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </ScrollArea>
          </PopoverContent>
        </Popover>

        <div className="h-6 w-px bg-border hidden sm:block" />

        {/* User Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-full px-2 py-1.5 text-sm text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary/50">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/20 text-primary border border-primary/30 shadow-[0_0_10px_-2px_hsl(var(--primary)/0.3)]">
                <User className="h-4 w-4" />
              </div>
              <span className="hidden sm:inline font-medium max-w-[100px] truncate">{user?.name || user?.username || 'User'}</span>
              <ChevronDown className="h-3 w-3 hidden sm:block opacity-50" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user?.name || user?.username || 'User'}</p>
                <p className="text-xs leading-none text-muted-foreground truncate">
                  {user?.email || 'user@devintel.ai'}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/settings" className="cursor-pointer w-full flex items-center">
                <UserIcon className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/settings" className="cursor-pointer w-full flex items-center">
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive cursor-pointer w-full flex items-center"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
