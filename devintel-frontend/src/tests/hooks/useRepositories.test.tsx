import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRepositories } from '@/hooks/useRepositories';
import { vi } from 'vitest';

vi.mock('@/lib/api', () => ({
    getRepositories: vi.fn(),
    addRepository: vi.fn(),
    deleteRepository: vi.fn(),
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });

    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useRepositories Hook', () => {
    it('fetches repositories successfully', async () => {
        const mockRepos = [
            { id: '1', full_name: 'user/repo1', indexed_status: true },
        ];

        const { getRepositories } = await import('@/lib/api');
        vi.mocked(getRepositories).mockResolvedValue(mockRepos);

        const { result } = renderHook(() => useRepositories(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => {
            expect(result.current.data).toEqual(mockRepos);
        });
    });

    it('handles error state', async () => {
        const { getRepositories } = await import('@/lib/api');
        vi.mocked(getRepositories).mockRejectedValue(new Error('Failed to fetch'));

        const { result } = renderHook(() => useRepositories(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => {
            expect(result.current.isError).toBe(true);
        });
    });

    it('shows loading state initially', () => {
        const { result } = renderHook(() => useRepositories(), {
            wrapper: createWrapper(),
        });

        expect(result.current.isLoading).toBe(true);
    });
});
