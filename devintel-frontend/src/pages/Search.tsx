import { useState, useEffect } from "react";
import { Search as SearchIcon, FileCode, ExternalLink, Loader2, Database, AlertCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRepositories } from "@/hooks/useRepositories";
import { useSearch } from "@/hooks/useSearch";

export default function SearchPage() {
    const { repos, loading: reposLoading } = useRepositories();
    const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
    const [query, setQuery] = useState("");

    const { results, loading, error, performSearch, clearResults } = useSearch(selectedRepoId || undefined);

    // Initialize selected repo
    useEffect(() => {
        if (repos.length > 0 && !selectedRepoId) {
            setSelectedRepoId(repos[0].id);
        }
    }, [repos, selectedRepoId]);

    const handleSearch = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!query.trim() || loading || !selectedRepoId) return;
        performSearch(query);
    };

    const selectedRepo = repos.find(r => r.id === selectedRepoId);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-6">
                <div>
                    <h1 className="text-2xl font-semibold flex items-center gap-2">
                        <SearchIcon className="h-6 w-6 text-primary" /> Semantic Search
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Find logic and patterns across your codebase using natural language
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Repository:</span>
                    <select
                        value={selectedRepoId || ""}
                        onChange={(e) => {
                            setSelectedRepoId(e.target.value);
                            clearResults();
                        }}
                        className="h-9 rounded-md border border-input bg-card px-3 py-1 text-sm outline-none focus:ring-1 focus:ring-primary min-w-[200px]"
                    >
                        {repos.map(r => (
                            <option key={r.id} value={r.id}>{r.repo_name}</option>
                        ))}
                        {repos.length === 0 && <option value="">No repos connected</option>}
                    </select>
                </div>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="relative group">
                <SearchIcon className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g. 'How is authentication implemented?' or 'Where are the API endpoints defined?'"
                    className="h-14 w-full rounded-2xl border border-input bg-card pl-12 pr-32 text-base text-foreground shadow-sm placeholder:text-muted-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    <Button
                        type="submit"
                        disabled={!query.trim() || loading || !selectedRepoId || !selectedRepo?.indexed_status}
                        className="h-10 px-6 rounded-xl gap-2 font-medium"
                    >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                        {loading ? "Searching..." : "Search"}
                    </Button>
                </div>
            </form>

            {!selectedRepo?.indexed_status && selectedRepoId && (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-warning/5 border border-warning/20 text-warning text-sm">
                    <AlertCircle className="h-4 w-4" />
                    <p>This repository hasn't been indexed yet. Please index it first to enable semantic search.</p>
                </div>
            )}

            {/* Results */}
            <div className="space-y-4">
                {loading && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <Loader2 className="h-10 w-10 text-primary animate-spin" />
                        <p className="text-sm text-muted-foreground animate-pulse">Scanning vector space for semantic matches...</p>
                    </div>
                )}

                {error && (
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-destructive/5 border border-destructive/20 text-destructive">
                        <AlertCircle className="h-4 w-4" />
                        <p className="text-sm">{error}</p>
                    </div>
                )}

                {!loading && results.length > 0 && (
                    <div className="grid gap-4">
                        <div className="flex items-center justify-between px-2">
                            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                                Found {results.length} relevant snippets
                            </span>
                        </div>
                        {results.map((result, idx) => (
                            <div
                                key={idx}
                                className="group overflow-hidden rounded-xl border border-border bg-card hover:border-primary/50 transition-all hover:shadow-md animate-in fade-in slide-in-from-bottom-2 duration-300"
                                style={{ animationDelay: `${idx * 50}ms` }}
                            >
                                <div className="flex items-center justify-between border-b border-border bg-muted/30 px-4 py-2">
                                    <div className="flex items-center gap-2 text-sm font-medium">
                                        <FileCode className="h-4 w-4 text-primary" />
                                        <span>{result.file_path}</span>
                                        <span className="rounded bg-accent px-1.5 py-0.5 text-[10px] text-muted-foreground">
                                            Chunk {result.chunk_index}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-[10px] font-bold text-success uppercase tracking-widest">
                                            {Math.round(result.similarity * 100)}% Match
                                        </span>
                                        <a
                                            href={selectedRepo?.url + '/blob/main/' + result.file_path}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-muted-foreground hover:text-primary transition-colors"
                                        >
                                            <ExternalLink className="h-3.5 w-3.5" />
                                        </a>
                                    </div>
                                </div>
                                <div className="p-4">
                                    <pre className="overflow-x-auto rounded-lg bg-accent/30 p-4 text-xs font-mono leading-relaxed text-foreground scrollbar-hide">
                                        <code>{result.chunk_text}</code>
                                    </pre>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {!loading && results.length === 0 && !error && query && (
                    <div className="flex flex-col items-center justify-center py-20 text-center opacity-50">
                        <Database className="h-12 w-12 mb-4 text-muted-foreground" />
                        <p className="text-lg font-medium">No matches found</p>
                        <p className="text-sm">Try rephrasing your search or using more descriptive terms.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
