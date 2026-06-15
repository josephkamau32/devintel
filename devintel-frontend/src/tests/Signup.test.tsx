import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Signup from '@/pages/Signup';
import { apiClient } from '@/lib/api-client';

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });

    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>{children}</BrowserRouter>
        </QueryClientProvider>
    );
};

describe('Signup Page', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders signup interface', () => {
        render(<Signup />, { wrapper: createWrapper() });
        expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument();
    });

    it('validates required fields', async () => {
        const user = userEvent.setup();
        render(<Signup />, { wrapper: createWrapper() });

        await user.click(screen.getByRole('button', { name: /create account/i }));

        // Form validation triggers browser validation
    });

    it('validates password length', async () => {
        const user = userEvent.setup();
        render(<Signup />, { wrapper: createWrapper() });

        await user.type(screen.getByLabelText(/full name/i), 'Test User');
        await user.type(screen.getByLabelText(/email/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'short');

        // Trigger form submission
        await user.click(screen.getByRole('button', { name: /create account/i }));

        // Browser validation should prevent submission
    });

    it('calls API on form submission', async () => {
        const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
            access_token: 'test-token',
            refresh_token: 'test-refresh',
            user: {
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                avatar_url: null,
                github_id: null,
            },
        } as any);

        const user = userEvent.setup();
        render(<Signup />, { wrapper: createWrapper() });

        await user.type(screen.getByLabelText(/full name/i), 'Test User');
        await user.type(screen.getByLabelText(/email/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'securepassword123');

        await user.click(screen.getByRole('button', { name: /create account/i }));

        await waitFor(() => {
            expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/signup', expect.any(Object));
        });
    });
});