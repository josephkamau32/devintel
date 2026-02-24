import apiClient from './api-client';

// ─── Chat ────────────────────────────────────────────────────────
export const sendChatMessage = async (message: string) => {
    return apiClient.post('/chat', { message });
};

export const getChatHistory = async () => {
    return apiClient.get('/chat/history');
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

/** List PRs for a specific repository. */
export const getRepositoryPulls = async (repositoryId: string): Promise<{ pulls: PullRequest[] }> => {
    return apiClient.get<{ pulls: PullRequest[] }>(`/api/v1/repos/${repositoryId}/pulls`);
};

/** Conduct a PR review. */
export const reviewPullRequest = async (data: PRReviewRequest): Promise<PRReviewResponse> => {
    return apiClient.post<PRReviewResponse>('/api/v1/pr-review', data);
};
