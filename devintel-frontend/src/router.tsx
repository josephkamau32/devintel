import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthGuard } from './components/AuthGuard';
import { Code2 } from 'lucide-react';

// Lazy-load pages for better code splitting
const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const SignupPage = lazy(() => import('./pages/SignupPage').then(m => ({ default: m.SignupPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const OAuthCallbackPage = lazy(() => import('./pages/OAuthCallbackPage').then(m => ({ default: m.OAuthCallbackPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));

function PageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0">
      <div className="flex flex-col items-center gap-4 animate-fade-in">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 animate-pulse-subtle">
          <Code2 className="h-5 w-5 text-white" />
        </div>
        <div className="h-1 w-16 rounded-full overflow-hidden bg-surface-3">
          <div className="h-full w-full bg-brand-500 rounded-full animate-shimmer" />
        </div>
      </div>
    </div>
  );
}

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

const router = createBrowserRouter([
  { path: '/', element: <SuspenseWrapper><LandingPage /></SuspenseWrapper> },
  { path: '/login', element: <SuspenseWrapper><LoginPage /></SuspenseWrapper> },
  { path: '/signup', element: <SuspenseWrapper><SignupPage /></SuspenseWrapper> },
  { path: '/oauth/callback', element: <SuspenseWrapper><OAuthCallbackPage /></SuspenseWrapper> },
  {
    element: <AuthGuard />,
    children: [
      { path: '/dashboard', element: <SuspenseWrapper><DashboardPage /></SuspenseWrapper> },
    ],
  },
  { path: '*', element: <SuspenseWrapper><NotFoundPage /></SuspenseWrapper> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
