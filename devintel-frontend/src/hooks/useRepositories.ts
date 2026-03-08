import { useState, useEffect, useCallback, useRef } from 'react';
import {
    getRepositories,
    getGithubRepos,
    connectRepository,
    deleteRepository,
    indexRepository,
    getRepoStatus,
    type RepoResponse,
    type GitHubRepo,
} from '@/lib/api';
import { useOrganization } from '@/contexts/OrganizationContext';

const POLL_INTERVAL_MS = 3000;

interface UseRepositoriesReturn {
    /** Connected repos from the backend. */
    repos: RepoResponse[];
    /** True while the initial fetch is in progress. */
    loading: boolean;
    /** Error message if the initial fetch failed. */
    error: string | null;
    /** Re-fetch the list from backend. */
    refresh: () => Promise<void>;
    /** GitHub repos available for connection (loaded on demand). */
    githubRepos: GitHubRepo[];
    /** True while GitHub repos are loading. */
    githubLoading: boolean;
    /** Error from GitHub repos fetch. */
    githubError: string | null;
    /** Fetch GitHub repos (call when opening the connect modal). */
    loadGithubRepos: () => Promise<void>;
    /** Connect + start indexing a GitHub repo. Returns the new repo or throws. */
    connectAndIndex: (ghRepo: GitHubRepo) => Promise<RepoResponse>;
    /** Delete a connected repo by ID. */
    removeRepo: (id: string) => Promise<void>;
    /** Trigger re-indexing for an existing repo. */
    reindexRepo: (id: string) => Promise<void>;
}

export function useRepositories(): UseRepositoriesReturn {
    const { currentOrganization } = useOrganization();

    const [repos, setRepos] = useState<RepoResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [githubRepos, setGithubRepos] = useState<GitHubRepo[]>([]);
    const [githubLoading, setGithubLoading] = useState(false);
    const [githubError, setGithubError] = useState<string | null>(null);

    // Track repos currently being polled
    const pollingRef = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

    // --- Polling logic -----------------------------------------------------------

    const stopPolling = useCallback((repoId: string) => {
        const interval = pollingRef.current.get(repoId);
        if (interval) {
            clearInterval(interval);
            pollingRef.current.delete(repoId);
        }
    }, []);

    const startPolling = useCallback(
        (repoId: string) => {
            // Don't double-poll
            if (pollingRef.current.has(repoId)) return;

            const interval = setInterval(async () => {
                try {
                    const status = await getRepoStatus(repoId);
                    setRepos((prev) =>
                        prev.map((r) =>
                            r.id === repoId
                                ? {
                                    ...r,
                                    indexed_status: status.indexed_status,
                                    indexing_progress: status.indexing_progress,
                                    indexing_error: status.indexing_error,
                                }
                                : r,
                        ),
                    );
                    // Stop polling once indexing is complete or errored
                    if (status.indexed_status || status.indexing_error) {
                        stopPolling(repoId);
                    }
                } catch {
                    // Silently fail — the user can refresh to recover
                    stopPolling(repoId);
                }
            }, POLL_INTERVAL_MS);

            pollingRef.current.set(repoId, interval);
        },
        [stopPolling],
    );

    // Cleanup all polls on unmount
    useEffect(() => {
        const polls = pollingRef.current;
        return () => {
            polls.forEach((interval) => clearInterval(interval));
            polls.clear();
        };
    }, []);

    // Auto-start polling for repos that are actively indexing
    useEffect(() => {
        repos.forEach((r) => {
            const isIndexing = !r.indexed_status && r.indexing_progress > 0 && !r.indexing_error;
            if (isIndexing) {
                startPolling(r.id);
            }
        });
    }, [repos, startPolling]);

    // --- Fetch connected repos ---------------------------------------------------

    const refresh = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getRepositories(currentOrganization?.id);
            setRepos(data.repositories);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }, message?: string };
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load repositories';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [currentOrganization?.id]);

    useEffect(() => {
        refresh();
    }, [refresh, currentOrganization?.id]);

    // --- GitHub repo list (on-demand) -------------------------------------------

    const loadGithubRepos = useCallback(async () => {
        setGithubLoading(true);
        setGithubError(null);
        try {
            const data = await getGithubRepos();
            setGithubRepos(data.repositories);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }, message?: string };
            const msg = err?.response?.data?.detail || err?.message || 'Failed to fetch GitHub repos';
            setGithubError(msg);
        } finally {
            setGithubLoading(false);
        }
    }, []);

    // --- Connect + Index ---------------------------------------------------------

    const connectAndIndex = useCallback(
        async (ghRepo: GitHubRepo): Promise<RepoResponse> => {
            const newRepo = await connectRepository({
                repo_name: ghRepo.repo_name,
                full_name: ghRepo.full_name,
                description: ghRepo.description,
                url: ghRepo.clone_url || ghRepo.url,
                stars: ghRepo.stars,
                language: ghRepo.language,
                org_id: currentOrganization?.id || null, // Associate with current org
            });

            // Add to local state immediately
            setRepos((prev) => [newRepo, ...prev]);

            // Kick off indexing (fire-and-forget — polling will pick it up)
            try {
                await indexRepository(newRepo.id);
                // Optimistically show progress starting
                setRepos((prev) =>
                    prev.map((r) =>
                        r.id === newRepo.id ? { ...r, indexing_progress: 1 } : r,
                    ),
                );
                startPolling(newRepo.id);
            } catch {
                // Indexing failed to start — repo is still saved, user can retry
            }

            return newRepo;
        },
        [startPolling, currentOrganization?.id],
    );

    // --- Delete ------------------------------------------------------------------

    const removeRepo = useCallback(async (id: string) => {
        await deleteRepository(id);
        stopPolling(id);
        setRepos((prev) => prev.filter((r) => r.id !== id));
    }, [stopPolling]);

    // --- Re-index ----------------------------------------------------------------

    const reindexRepo = useCallback(
        async (id: string) => {
            await indexRepository(id);
            setRepos((prev) =>
                prev.map((r) =>
                    r.id === id
                        ? { ...r, indexed_status: false, indexing_progress: 1, indexing_error: null }
                        : r,
                ),
            );
            startPolling(id);
        },
        [startPolling],
    );

    return {
        repos,
        loading,
        error,
        refresh,
        githubRepos,
        githubLoading,
        githubError,
        loadGithubRepos,
        connectAndIndex,
        removeRepo,
        reindexRepo,
    };
}
