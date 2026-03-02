/**
 * Shared TypeScript interfaces for the DevIntel AI platform.
 */

export interface Repository {
    id: string;
    repo_name: string;
    full_name: string;
    url: string;
    description?: string | null;
    language?: string | null;
    stars: number;
    user_id?: string;
    indexed_status: boolean;
    last_indexed_at?: string | null;
    indexing_error?: string | null;
    indexing_progress: number;
    created_at?: string;
    updated_at?: string;
}

export interface GitHubRepo {
    repo_name: string;
    full_name: string;
    description: string | null;
    url: string;
    clone_url: string;
    stars: number;
    language: string | null;
    private: boolean;
}

export interface ChatMessageData {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    tokenUsage?: number;
    responseTimeMs?: number;
}

export interface AnalyticsDashboard {
    total_queries: number;
    total_tokens: number;
    total_repos_indexed: number;
    usage_trend: { date: string; queries: number }[];
    top_repositories: { repo_name: string; queries: number }[];
    last_active_at: string | null;
}

export interface PullRequest {
    id: string;
    title: string;
    author: string;
    authorAvatar: string;
    status: 'open' | 'merged' | 'closed';
    createdAt: string;
    repository: string;
    additions: number;
    deletions: number;
    number?: number;
    html_url?: string;
    aiSummary?: string;
    suggestedChanges?: string[];
}

export interface ActivityItem {
    id: string;
    type: 'index' | 'chat' | 'pr_review' | 'alert';
    message: string;
    timestamp: string;
}

export interface AnalyticsData {
    aiUsage: { date: string; queries: number }[];
    topFiles: { file: string; queries: number }[];
    complexity: { date: string; score: number }[];
}
