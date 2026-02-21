/**
 * Shared TypeScript interfaces for the DevIntel AI platform.
 */

export interface Repository {
    id: string;
    name: string;
    full_name: string;
    url?: string;
    description?: string;
    language?: string;
    stars?: number;
    indexed_status?: string;
    indexing_progress?: number;
    indexing_error?: string;
    created_at?: string;
    updated_at?: string;
}

export interface GitHubRepo {
    id: number;
    name: string;
    full_name: string;
    html_url: string;
    description: string | null;
    language: string | null;
    stargazers_count: number;
    private: boolean;
    updated_at: string;
}

export interface ChatMessageData {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
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
