import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorBoundary } from '../components/ErrorBoundary';

// Component that throws error
const ThrowError = () => {
    throw new Error('Test error');
};

// Normal component
const NormalComponent = () => <div>Normal content</div>;

describe('ErrorBoundary', () => {
    it('renders children when no error', () => {
        render(
            <ErrorBoundary>
                <NormalComponent />
            </ErrorBoundary>
        );

        expect(screen.getByText('Normal content')).toBeInTheDocument();
    });

    it('displays error UI when child throws', () => {
        // Suppress console.error for this test
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

        render(
            <ErrorBoundary>
                <ThrowError />
            </ErrorBoundary>
        );

        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

        consoleSpy.mockRestore();
    });

    it('shows try again button', () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

        render(
            <ErrorBoundary>
                <ThrowError />
            </ErrorBoundary>
        );

        const button = screen.getByRole('button', { name: /try again/i });
        expect(button).toBeInTheDocument();

        consoleSpy.mockRestore();
    });

    it('resets error when try again clicked', () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

        const { rerender } = render(
            <ErrorBoundary>
                <ThrowError />
            </ErrorBoundary>
        );

        const button = screen.getByRole('button', { name: /try again/i });
        fireEvent.click(button);

        // After reset, re-render with normal component
        rerender(
            <ErrorBoundary>
                <NormalComponent />
            </ErrorBoundary>
        );

        expect(screen.getByText('Normal content')).toBeInTheDocument();

        consoleSpy.mockRestore();
    });
});
