import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { queryClient } from './lib/queryClient';
import { AppRouter } from './router';
import { ErrorBoundary } from './components/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppRouter />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#111114',
              color: '#fafafa',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: '500',
              boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4), 0 4px 8px rgba(0, 0, 0, 0.25)',
              padding: '10px 14px',
            },
            success: {
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fafafa',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fafafa',
              },
            },
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
