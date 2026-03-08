import { useState, useCallback } from 'react';
import { searchRepository, type SearchResult } from '@/lib/api';

export function useSearch(repositoryId?: string) {
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const performSearch = useCallback(async (query: string) => {
        if (!repositoryId || !query.trim()) return;

        setLoading(true);
        setError(null);
        try {
            const data = await searchRepository(repositoryId, query);
            setResults(data.results);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }, message?: string };
            const msg = err?.response?.data?.detail || err?.message || 'Failed to perform search';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [repositoryId]);

    const clearResults = useCallback(() => {
        setResults([]);
        setError(null);
    }, []);

    return {
        results,
        loading,
        error,
        performSearch,
        clearResults,
    };
}
