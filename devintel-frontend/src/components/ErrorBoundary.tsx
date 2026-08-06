import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[DevIntel] Uncaught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4">
          <div className="w-full max-w-sm text-center animate-fade-in">
            <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-status-error-muted border border-status-error/20">
              <AlertTriangle className="h-6 w-6 text-status-error" />
            </div>
            <h2 className="text-h3 text-text-primary mb-2">Something went wrong</h2>
            <p className="text-body text-text-tertiary mb-6">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <div className="flex flex-col items-center gap-2 sm:flex-row sm:justify-center">
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.reload();
                }}
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-500"
              >
                <RotateCw className="h-4 w-4" />
                Try again
              </button>
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.href = '/';
                }}
                className="inline-flex items-center gap-2 rounded-lg border border-border-medium px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary hover:bg-surface-3"
              >
                <Home className="h-4 w-4" />
                Go home
              </button>
            </div>
            <a
              href="https://github.com/josephkamau32/devintel/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block text-xs text-text-quaternary hover:text-text-tertiary transition-colors"
            >
              Report this issue →
            </a>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
