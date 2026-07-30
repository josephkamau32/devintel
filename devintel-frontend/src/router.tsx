import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthGuard } from './components/AuthGuard';

// Lazy-load pages for better code splitting
const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const SignupPage = lazy(() => import('./pages/SignupPage').then(m => ({ default: m.SignupPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const OAuthCallbackPage = lazy(() => import('./pages/OAuthCallbackPage').then(m => ({ default: m.OAuthCallbackPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));

function PageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-violet-600 border-t-transparent" />
        <p className="text-sm text-slate-400">Loading…</p>
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
