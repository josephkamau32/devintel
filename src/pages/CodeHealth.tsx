import { useState, useEffect } from "react";
import {
    Shield,
    FileText,
    Wrench,
    TestTube,
    Lock,
    GitBranch,
    Loader2,
    RefreshCw,
    AlertTriangle,
    Lightbulb,
    ChevronDown,
    Check,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { CodeHealthReport, Repository } from "@/lib/types";

/** Colour coding for scores */
function scoreColor(score: number) {
    if (score >= 75) return "text-green-400";
    if (score >= 50) return "text-amber-400";
    return "text-red-400";
}

function scoreRingColor(score: number) {
    if (score >= 75) return "#22c55e";
    if (score >= 50) return "#f59e0b";
    return "#ef4444";
}

function scoreLabel(score: number) {
    if (score >= 80) return "Excellent";
    if (score >= 65) return "Good";
    if (score >= 50) return "Fair";
    if (score >= 35) return "Poor";
    return "Critical";
}

/** Radial gauge SVG — single-ring progress arc */
function ScoreGauge({ score }: { score: number }) {
    const radius = 72;
    const circ = 2 * Math.PI * radius;
    const offset = circ - (score / 100) * circ;
    const color = scoreRingColor(score);

    return (
        <div className="relative flex items-center justify-center">
            <svg width="180" height="180" viewBox="0 0 180 180" className="-rotate-90">
                <circle cx="90" cy="90" r={radius} fill="none" stroke="hsl(222,16%,16%)" strokeWidth="14" />
                <circle
                    cx="90"
                    cy="90"
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth="14"
                    strokeDasharray={circ}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    style={{ transition: "stroke-dashoffset 1s ease" }}
                />
            </svg>
            <div className="absolute flex flex-col items-center">
                <span className={`text-4xl font-bold ${scoreColor(score)}`}>{Math.round(score)}</span>
                <span className="text-xs text-muted-foreground mt-1">{scoreLabel(score)}</span>
            </div>
        </div>
    );
}

/** Generic dimension bar */
function DimensionBar({
    icon: Icon,
    label,
    score,
}: {
    icon: React.ElementType;
    label: string;
    score: number;
}) {
    const color = scoreRingColor(score);
    return (
        <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                </span>
                <span className={`font-semibold ${scoreColor(score)}`}>{Math.round(score)}</span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div
                    className="h-2 rounded-full transition-all duration-700"
                    style={{ width: `${score}%`, backgroundColor: color }}
                />
            </div>
        </div>
    );
}

export default function CodeHealthPage() {
    const [repos, setRepos] = useState<Repository[]>([]);
    const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
    const [health, setHealth] = useState<CodeHealthReport | null>(null);
    const [loadingRepos, setLoadingRepos] = useState(true);
    const [loadingHealth, setLoadingHealth] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [dropdownOpen, setDropdownOpen] = useState(false);

    // Load repos
    useEffect(() => {
        apiClient
            .get<{ repositories: Repository[] }>("/api/v1/repos")
            .then((d) => {
                const list = d.repositories || [];
                setRepos(list);
                const indexed = list.find((r) => r.indexed_status);
                if (indexed) setSelectedRepo(indexed);
            })
            .finally(() => setLoadingRepos(false));
    }, []);

    // Load health when repo changes
    useEffect(() => {
        if (!selectedRepo) return;
        setHealth(null);
        setError(null);
        setLoadingHealth(true);
        apiClient
            .get<CodeHealthReport>(`/api/v1/repos/${selectedRepo.id}/health`)
            .then(setHealth)
            .catch((e) => {
                const msg = e?.response?.data?.detail || e?.message || "Failed to load health report";
                setError(msg);
            })
            .finally(() => setLoadingHealth(false));
    }, [selectedRepo]);

    async function handleRefresh() {
        if (!selectedRepo) return;
        setRefreshing(true);
        setError(null);
        try {
            await apiClient.post(`/api/v1/repos/${selectedRepo.id}/health/refresh`);
            // Poll for result
            let attempts = 0;
            const poll = setInterval(async () => {
                attempts++;
                try {
                    const result = await apiClient.get<CodeHealthReport>(
                        `/api/v1/repos/${selectedRepo.id}/health`
                    );
                    const prev = health?.computed_at;
                    if (!prev || result.computed_at !== prev) {
                        setHealth(result);
                        setRefreshing(false);
                        clearInterval(poll);
                    }
                } catch {
                    // Still computing
                }
                if (attempts > 30) {
                    clearInterval(poll);
                    setRefreshing(false);
                }
            }, 3000);
        } catch (e: any) {
            setError(e?.response?.data?.detail || "Failed to trigger refresh");
            setRefreshing(false);
        }
    }

    const indexedRepos = repos.filter((r) => r.indexed_status);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold">Code Health</h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        AI-powered quality analysis of your indexed repository
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    {/* Repo selector */}
                    <div className="relative">
                        <button
                            onClick={() => setDropdownOpen((v) => !v)}
                            className="flex items-center gap-2 h-9 rounded-lg border border-input bg-card px-3 text-sm text-foreground hover:border-primary transition-colors"
                        >
                            <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="max-w-[180px] truncate">
                                {selectedRepo ? selectedRepo.full_name : "Select repository"}
                            </span>
                            <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
                        </button>
                        {dropdownOpen && (
                            <div className="absolute right-0 top-full mt-1 z-50 w-64 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
                                {indexedRepos.length === 0 ? (
                                    <p className="px-3 py-2.5 text-sm text-muted-foreground">No indexed repositories</p>
                                ) : (
                                    indexedRepos.map((r) => (
                                        <button
                                            key={r.id}
                                            onClick={() => { setSelectedRepo(r); setDropdownOpen(false); }}
                                            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent transition-colors"
                                        >
                                            <span className="flex-1 truncate">{r.full_name}</span>
                                            {selectedRepo?.id === r.id && <Check className="h-3.5 w-3.5 text-primary" />}
                                        </button>
                                    ))
                                )}
                            </div>
                        )}
                    </div>

                    {/* Refresh */}
                    {selectedRepo && (
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing || loadingHealth}
                            className="flex items-center gap-1.5 h-9 rounded-lg border border-input bg-card px-3 text-sm text-muted-foreground hover:text-foreground hover:border-primary transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
                            {refreshing ? "Analyzing…" : "Refresh"}
                        </button>
                    )}
                </div>
            </div>

            {/* Loading */}
            {(loadingHealth || loadingRepos) && (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-7 w-7 animate-spin text-muted-foreground" />
                </div>
            )}

            {/* Error */}
            {!loadingHealth && error && (
                <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
                    <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-amber-400">Health report unavailable</p>
                        <p className="mt-1 text-xs text-muted-foreground">{error}</p>
                        {refreshing === false && selectedRepo && (
                            <button
                                onClick={handleRefresh}
                                className="mt-2 text-xs text-primary hover:underline"
                            >
                                Trigger analysis →
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* No repo selected */}
            {!loadingRepos && !selectedRepo && !error && (
                <div className="flex flex-col items-center justify-center py-20 rounded-xl border border-dashed border-border">
                    <Shield className="h-10 w-10 text-muted-foreground" />
                    <p className="mt-3 text-sm font-medium">Select an indexed repository</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                        Health reports are generated automatically after indexing
                    </p>
                </div>
            )}

            {/* Health Report */}
            {!loadingHealth && health && (
                <>
                    {/* Top row: gauge + dimensions */}
                    <div className="grid gap-6 lg:grid-cols-3">
                        {/* Overall Score */}
                        <div className="rounded-xl border border-border bg-card p-6 flex flex-col items-center gap-4">
                            <h2 className="font-semibold text-card-foreground self-start">Overall Score</h2>
                            <ScoreGauge score={health.overall_score} />
                            <div className="w-full text-center space-y-1">
                                <p className="text-xs text-muted-foreground">{health.language_detected || "Unknown"} repository</p>
                                <p className="text-xs text-muted-foreground">{health.files_analyzed} file chunks analyzed</p>
                                {health.computed_at && (
                                    <p className="text-xs text-muted-foreground">
                                        Computed {new Date(health.computed_at).toLocaleString()}
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Dimension Breakdown */}
                        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-5">
                            <h2 className="font-semibold text-card-foreground">Dimension Breakdown</h2>
                            <DimensionBar icon={Wrench} label="Complexity" score={health.dimensions.complexity} />
                            <DimensionBar icon={FileText} label="Documentation" score={health.dimensions.documentation} />
                            <DimensionBar icon={Shield} label="Maintainability" score={health.dimensions.maintainability} />
                            <DimensionBar icon={TestTube} label="Test Coverage" score={health.dimensions.test_coverage} />
                            <DimensionBar icon={Lock} label="Security" score={health.dimensions.security} />
                        </div>
                    </div>

                    {/* Summary */}
                    <div className="rounded-xl border border-border bg-card p-5">
                        <h2 className="font-semibold text-card-foreground mb-3">Executive Summary</h2>
                        <p className="text-sm text-muted-foreground leading-relaxed">{health.summary}</p>
                    </div>

                    {/* Issues + Recommendations */}
                    <div className="grid gap-6 lg:grid-cols-2">
                        {health.top_issues.length > 0 && (
                            <div className="rounded-xl border border-border bg-card p-5">
                                <h2 className="font-semibold text-card-foreground mb-3 flex items-center gap-2">
                                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                                    Top Issues
                                </h2>
                                <ul className="space-y-2">
                                    {health.top_issues.map((issue, i) => (
                                        <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                                            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                                            {issue}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {health.recommendations.length > 0 && (
                            <div className="rounded-xl border border-border bg-card p-5">
                                <h2 className="font-semibold text-card-foreground mb-3 flex items-center gap-2">
                                    <Lightbulb className="h-4 w-4 text-primary" />
                                    Recommendations
                                </h2>
                                <ul className="space-y-2">
                                    {health.recommendations.map((rec, i) => (
                                        <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                                            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                                            {rec}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
