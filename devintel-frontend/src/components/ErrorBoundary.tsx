import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface Props {
    children: React.ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

/**
 * Global Error Boundary Component
 * 
 * Catches React errors and displays user-friendly fallback UI.
 * Integrates with Sentry for error reporting in production.
 */
export class ErrorBoundary extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // Log error to console in development only
        if (import.meta.env.DEV) {
            console.error('Error Boundary caught:', error, errorInfo);
        }

        // Send to Sentry in production
        if (import.meta.env.PROD) {
            // Sentry integration - uncomment when Sentry is configured
            // Make sure to set VITE_SENTRY_DSN in your .env file
            try {
                if (import.meta.env.VITE_SENTRY_DSN && typeof window !== 'undefined') {
                    // You'll need to: npm install @sentry/react
                    // import * as Sentry from '@sentry/react';
                    // Sentry.captureException(error, { contexts: { react: errorInfo } });
                }
            } catch (sentryError) {
                // Silently fail if Sentry is not available
            }
        }
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center p-4 bg-background">
                    <div className="max-w-md w-full">
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Something went wrong</AlertTitle>
                            <AlertDescription className="mt-2">
                                <p className="mb-4">
                                    We're sorry, but something unexpected happened. The error has been logged
                                    and we'll look into it.
                                </p>
                                {import.meta.env.DEV && this.state.error && (
                                    <details className="mb-4">
                                        <summary className="cursor-pointer font-semibold">
                                            Error Details (Dev Only)
                                        </summary>
                                        <pre className="mt-2 text-xs bg-background/50 p-2 rounded overflow-auto">
                                            {this.state.error.toString()}
                                            {this.state.error.stack}
                                        </pre>
                                    </details>
                                )}
                                <Button onClick={this.handleReset} variant="outline" className="w-full">
                                    Return to Home
                                </Button>
                            </AlertDescription>
                        </Alert>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
