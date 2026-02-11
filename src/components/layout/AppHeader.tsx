import { Search, Bell, ChevronDown, User } from "lucide-react";
import { useState } from "react";

export function AppHeader() {
  const [searchFocused, setSearchFocused] = useState(false);

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      {/* Search */}
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search repositories, files, or ask AI..."
          className={`h-9 w-full rounded-md border bg-accent pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none transition-colors ${
            searchFocused ? "border-primary" : "border-border"
          }`}
          onFocus={() => setSearchFocused(true)}
          onBlur={() => setSearchFocused(false)}
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
          ⌘K
        </kbd>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <button className="relative flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary" />
        </button>

        <div className="h-6 w-px bg-border" />

        <button className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary">
            <User className="h-4 w-4" />
          </div>
          <span className="hidden sm:inline">John Doe</span>
          <ChevronDown className="h-3 w-3" />
        </button>
      </div>
    </header>
  );
}
