import { useState, useCallback, useEffect } from 'react';
import { getAnalyticsDashboard, type AnalyticsDashboard } from '@/lib/api';

export function useAnalytics() {
    const [data, setData] = useState<AnalyticsDashboard | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await getAnalyticsDashboard();
            setData(result);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }, message?: string };
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load analytics';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return {
        data,
        loading,
        error,
        refresh,
    };
}
