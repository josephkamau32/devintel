import apiClient from './api-client';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
}

export interface ChatHistoryResponse {
    messages: ChatMessage[];
    repository_id: string;
}

export const sendChatMessage = async (data: {
    question: string,
    repository_id: string,
    chat_history?: ChatMessage[]
}) => {
    return apiClient.post('/api/v1/chat', data);
};

export const getChatHistory = async (repositoryId: string): Promise<ChatHistoryResponse> => {
    return apiClient.get<ChatHistoryResponse>(`/api/v1/chat/history/${repositoryId}`);
};

// ─── Repositories ────────────────────────────────────────────────

export interface RepoResponse {
    id: string;
    user_id: string;
    repo_name: string;
    full_name: string;
    description: string | null;
    url: string;
    stars: number;
    language: string | null;
    indexed_status: boolean;
    last_indexed_at: string | null;
    indexing_error: string | null;
    indexing_progress: number;
    created_at: string;
    updated_at: string;
}

export interface RepoListResponse {
    repositories: RepoResponse[];
    total: number;
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

export interface RepoStatusResponse {
    id: string;
    indexed_status: boolean;
    indexing_progress: number;
    indexing_error: string | null;
}

/** List the user's connected (saved) repositories. */
export const getRepositories = async (): Promise<RepoListResponse> => {
    return apiClient.get<RepoListResponse>('/api/v1/repos');
};

/** Fetch repos from the user's GitHub account. */
export const getGithubRepos = async (page = 1, perPage = 30): Promise<{ repositories: GitHubRepo[] }> => {
    return apiClient.get<{ repositories: GitHubRepo[] }>(`/api/v1/repos/github?page=${page}&per_page=${perPage}`);
};

/** Save (connect) a repository to the user's account. */
export const connectRepository = async (data: {
    repo_name: string;
    full_name: string;
    description?: string | null;
    url: string;
    stars?: number;
    language?: string | null;
}): Promise<RepoResponse> => {
    return apiClient.post<RepoResponse>('/api/v1/repos', data);
};

/** Delete a connected repository. */
export const deleteRepository = async (id: string): Promise<void> => {
    return apiClient.delete(`/api/v1/repos/${id}`);
};

/** Trigger indexing for a repository. */
export const indexRepository = async (repositoryId: string): Promise<{ task_id: string; message: string }> => {
    return apiClient.post<{ task_id: string; message: string }>('/api/v1/repos/index', {
        repository_id: repositoryId,
    });
};

/** Lightweight status poll for a single repo. */
export const getRepoStatus = async (id: string): Promise<RepoStatusResponse> => {
    return apiClient.get<RepoStatusResponse>(`/api/v1/repos/${id}/status`);
};

// ─── Pull Requests ─────────────────────────────────────────────

export interface PullRequest {
    number: number;
    title: string;
    state: string;
    author: string;
    author_avatar: string | null;
    created_at: string;
    updated_at: string;
    additions: number;
    deletions: number;
    url: string;
}

export interface PRReviewRequest {
    repository_id: string;
    pr_number?: number;
    pull_request_diff?: string;
    pr_title: string;
    pr_description?: string;
}

export interface PRReviewResponse {
    summary: string;
    potential_issues: string[];
    refactoring_suggestions: string[];
    security_warnings: string[];
    performance_notes: string[];
}

export interface SearchResult {
    file_path: string;
    chunk_text: string;
    similarity: number;
    chunk_index: number;
}

export interface SearchResponse {
    results: SearchResult[];
    repository_id: string;
    query: string;
}

/** List PRs for a specific repository. */
export const getRepositoryPulls = async (repositoryId: string): Promise<{ pulls: PullRequest[] }> => {
    return apiClient.get<{ pulls: PullRequest[] }>(`/api/v1/repos/${repositoryId}/pulls`);
};

/** conduct a PR review. */
export const reviewPullRequest = async (data: PRReviewRequest): Promise<PRReviewResponse> => {
    return apiClient.post<PRReviewResponse>('/api/v1/pr-review', data);
};

export interface UsageTrend {
    date: string;
    queries: number;
}

export interface RepoUsage {
    repo_name: string;
    queries: number;
}

export interface AnalyticsDashboard {
    total_queries: number;
    total_tokens: number;
    total_repos_indexed: number;
    usage_trend: UsageTrend[];
    top_repositories: RepoUsage[];
    last_active_at: string | null;
}

/** Perform semantic search in a repository. */
export const searchRepository = async (repositoryId: string, query: string, topK = 10): Promise<SearchResponse> => {
    return apiClient.get<SearchResponse>(`/api/v1/repos/${repositoryId}/search?q=${encodeURIComponent(query)}&top_k=${topK}`);
};

/** Get real-time analytics dashboard data. */
export const getAnalyticsDashboard = async (): Promise<AnalyticsDashboard> => {
    return apiClient.get<AnalyticsDashboard>('/api/v1/analytics/dashboard');
};
