import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
    LayoutDashboard, GitBranch, MessageSquare, GitPullRequest,
    BarChart3, Settings, Search, Command, ArrowRight
} from "lucide-react";

interface CommandItem {
    id: string;
    label: string;
    description: string;
    icon: React.ElementType;
    action: () => void;
    keywords: string[];
}

interface CommandPaletteProps {
    open: boolean;
    onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
    const navigate = useNavigate();
    const [query, setQuery] = useState("");
    const [activeIndex, setActiveIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    const go = useCallback((path: string) => {
        navigate(path);
        onClose();
    }, [navigate, onClose]);

    const allCommands: CommandItem[] = [
        {
            id: "dashboard",
            label: "Dashboard",
            description: "Overview and stats",
            icon: LayoutDashboard,
            action: () => go("/dashboard"),
            keywords: ["home", "overview", "stats"],
        },
        {
            id: "repositories",
            label: "Repositories",
            description: "Manage and index your repos",
            icon: GitBranch,
            action: () => go("/repositories"),
            keywords: ["repo", "repos", "index", "connect", "github"],
        },
        {
            id: "chat",
            label: "AI Chat",
            description: "Chat with your codebase",
            icon: MessageSquare,
            action: () => go("/chat"),
            keywords: ["chat", "ai", "ask", "question", "rag", "code"],
        },
        {
            id: "pull-requests",
            label: "Pull Requests",
            description: "AI-powered code reviews",
            icon: GitPullRequest,
            action: () => go("/pull-requests"),
            keywords: ["pr", "pull", "review", "diff", "merge"],
        },
        {
            id: "analytics",
            label: "Analytics",
            description: "Usage insights and trends",
            icon: BarChart3,
            action: () => go("/analytics"),
            keywords: ["analytics", "usage", "stats", "tokens", "chart"],
        },
        {
            id: "settings",
            label: "Settings",
            description: "Profile and preferences",
            icon: Settings,
            action: () => go("/settings"),
            keywords: ["settings", "profile", "account", "preferences"],
        },
    ];

    const filtered = query.trim()
        ? allCommands.filter(cmd => {
            const q = query.toLowerCase();
            return (
                cmd.label.toLowerCase().includes(q) ||
                cmd.description.toLowerCase().includes(q) ||
                cmd.keywords.some(k => k.includes(q))
            );
        })
        : allCommands;

    // Reset state when palette opens
    useEffect(() => {
        if (open) {
            setQuery("");
            setActiveIndex(0);
            setTimeout(() => inputRef.current?.focus(), 30);
        }
    }, [open]);

    // Reset active index when filter changes
    useEffect(() => {
        setActiveIndex(0);
    }, [query]);

    // Scroll active item into view
    useEffect(() => {
        const activeEl = listRef.current?.querySelector(`[data-index="${activeIndex}"]`);
        activeEl?.scrollIntoView({ block: "nearest" });
    }, [activeIndex]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "ArrowDown") {
            e.preventDefault();
            setActiveIndex(i => Math.min(i + 1, filtered.length - 1));
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActiveIndex(i => Math.max(i - 1, 0));
        } else if (e.key === "Enter") {
            e.preventDefault();
            filtered[activeIndex]?.action();
        } else if (e.key === "Escape") {
            onClose();
        }
    };

    if (!open) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4"
            onClick={onClose}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />

            {/* Palette */}
            <div
                className="relative w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl overflow-hidden animate-slide-up"
                onClick={e => e.stopPropagation()}
            >
                {/* Search input */}
                <div className="flex items-center gap-3 px-4 border-b border-border">
                    <Search className="h-4 w-4 text-muted-foreground shrink-0" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Search pages and actions..."
                        className="h-12 flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
                    />
                    <kbd className="hidden sm:flex items-center gap-1 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground font-mono shrink-0">
                        esc
                    </kbd>
                </div>

                {/* Results */}
                <div ref={listRef} className="max-h-80 overflow-auto p-2">
                    {filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                            <Search className="h-6 w-6 mb-2 opacity-40" />
                            <p className="text-sm">No results for "{query}"</p>
                        </div>
                    ) : (
                        filtered.map((cmd, i) => {
                            const Icon = cmd.icon;
                            const isActive = i === activeIndex;
                            return (
                                <button
                                    key={cmd.id}
                                    data-index={i}
                                    onClick={cmd.action}
                                    onMouseEnter={() => setActiveIndex(i)}
                                    className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors ${isActive ? "bg-primary/10 text-foreground" : "text-card-foreground hover:bg-accent"
                                        }`}
                                >
                                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${isActive ? "border-primary/30 bg-primary/10 text-primary" : "border-border bg-muted text-muted-foreground"
                                        }`}>
                                        <Icon className="h-4 w-4" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{cmd.label}</p>
                                        <p className="text-xs text-muted-foreground truncate">{cmd.description}</p>
                                    </div>
                                    {isActive && <ArrowRight className="h-4 w-4 text-primary shrink-0" />}
                                </button>
                            );
                        })
                    )}
                </div>

                {/* Footer hint */}
                <div className="border-t border-border px-4 py-2 flex items-center gap-4 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                        <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono">↑↓</kbd>
                        navigate
                    </span>
                    <span className="flex items-center gap-1">
                        <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono">↵</kbd>
                        open
                    </span>
                    <span className="flex items-center gap-1">
                        <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono">esc</kbd>
                        close
                    </span>
                </div>
            </div>
        </div>
    );
}
