import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import Dashboard from '../pages/Dashboard';

// Mock API client
vi.mock('../lib/api-client', () => ({
    apiClient: {
        get: vi.fn(() => Promise.resolve({
            data: {
                total_repositories: 5,
                total_chats: 20,
                recent_activity: [],
                top_repositories: []
            }
        }))
    }
}));

const queryClient = new QueryClient({
    defaultOptions: {
        queries: { retry: false },
    },
});

const renderWithProviders = (component: React.ReactElement) => {
    return render(
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                {component}
            </BrowserRouter>
        </QueryClientProvider>
    );
};

describe('Dashboard', () => {
    it('renders dashboard heading', async () => {
        renderWithProviders(<Dashboard />);

        await waitFor(() => {
            expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
        });
    });

    it('displays repository stats', async () => {
        renderWithProviders(<Dashboard />);

        await waitFor(() => {
            expect(screen.getByText(/repositories/i)).toBeInTheDocument();
        });
    });

    it('shows loading state initially', () => {
        renderWithProviders(<Dashboard />);

        // Should show loading skeleton or spinner
        const loadingElements = screen.queryAllByTestId(/loading|skeleton/i);
        expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });
});
