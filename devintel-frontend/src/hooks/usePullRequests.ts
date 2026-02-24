import { useState, useCallback } from 'react';
import { getRepositoryPulls, reviewPullRequest, type PullRequest, type PRReviewResponse } from '@/lib/api';

export function usePullRequests(repositoryId?: string) {
    const [pulls, setPulls] = useState<PullRequest[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [reviewing, setReviewing] = useState<number | null>(null); // PR number being reviewed

    const fetchPulls = useCallback(async (id?: string) => {
        const targetId = id || repositoryId;
        if (!targetId) return;

        setLoading(true);
        setError(null);
        try {
            const data = await getRepositoryPulls(targetId);
            setPulls(data.pulls);
        } catch (e: any) {
            const msg = e?.response?.data?.detail || e?.message || 'Failed to fetch pull requests';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [repositoryId]);

    const performReview = useCallback(async (pr: PullRequest): Promise<PRReviewResponse> => {
        if (!repositoryId) throw new Error("No repository selected");

        setReviewing(pr.number);
        try {
            const result = await reviewPullRequest({
                repository_id: repositoryId,
                pr_number: pr.number,
                pr_title: pr.title,
            });
            return result;
        } finally {
            setReviewing(null);
        }
    }, [repositoryId]);

    return {
        pulls,
        loading,
        error,
        reviewing,
        fetchPulls,
        performReview,
    };
}
