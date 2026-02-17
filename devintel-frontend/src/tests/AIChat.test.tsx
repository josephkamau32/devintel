import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import AIChat from '@/pages/AIChat';

vi.mock('@/lib/api', () => ({
    sendChatMessage: vi.fn(),
    getChatHistory: vi.fn(),
}));

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

describe('AIChat Component', () => {
    it('renders chat interface', () => {
        render(<AIChat />, { wrapper: createWrapper() });
        expect(screen.getByPlaceholderText(/ask about your code/i)).toBeInTheDocument();
    });

    it('allows user to type a message', async () => {
        const user = userEvent.setup();
        render(<AIChat />, { wrapper: createWrapper() });

        const input = screen.getByPlaceholderText(/ask about your code/i);
        await user.type(input, 'What does this function do?');

        expect(input).toHaveValue('What does this function do?');
    });

    it('sends message when user submits', async () => {
        const user = userEvent.setup();
        const { sendChatMessage } = await import('@/lib/api');
        vi.mocked(sendChatMessage).mockResolvedValue({
            message: 'This function calculates the sum',
        });

        render(<AIChat />, { wrapper: createWrapper() });

        const input = screen.getByPlaceholderText(/ask about your code/i);
        await user.type(input, 'Explain this code');

        const submitButton = screen.getByRole('button', { name: /send/i });
        await user.click(submitButton);

        await waitFor(() => {
            expect(sendChatMessage).toHaveBeenCalledWith(
                expect.objectContaining({
                    question: 'Explain this code',
                })
            );
        });
    });

    it('displays chat history', async () => {
        const { getChatHistory } = await import('@/lib/api');
        const mockHistory = [
            { user: 'What is RAG?', assistant: 'RAG is Retrieval Augmented Generation' },
        ];
        vi.mocked(getChatHistory).mockResolvedValue(mockHistory);

        render(<AIChat />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('What is RAG?')).toBeInTheDocument();
            expect(screen.getByText(/Retrieval Augmented Generation/i)).toBeInTheDocument();
        });
    });

    it('handles empty input validation', async () => {
        const user = userEvent.setup();
        render(<AIChat />, { wrapper: createWrapper() });

        const submitButton = screen.getByRole('button', { name: /send/i });
        await user.click(submitButton);

        // Should not call API with empty message
        const { sendChatMessage } = await import('@/lib/api');
        expect(sendChatMessage).not.toHaveBeenCalled();
    });
});
