import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthGuard } from './components/AuthGuard';
import { Code2 } from 'lucide-react';

// ─── Lazy-load pages ───
const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const SignupPage = lazy(() => import('./pages/SignupPage').then(m => ({ default: m.SignupPage })));
const OAuthCallbackPage = lazy(() => import('./pages/OAuthCallbackPage').then(m => ({ default: m.OAuthCallbackPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));

// ─── Authenticated pages ───
const AppLayout = lazy(() => import('./components/layout/AppLayout').then(m => ({ default: m.AppLayout })));
const IntelligenceDashboard = lazy(() => import('./pages/IntelligenceDashboard').then(m => ({ default: m.IntelligenceDashboard })));
const RepositoriesPage = lazy(() => import('./pages/RepositoriesPage').then(m => ({ default: m.RepositoriesPage })));
const RepositoryWorkspace = lazy(() => import('./pages/RepositoryWorkspace').then(m => ({ default: m.RepositoryWorkspace })));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const InsightsPage = lazy(() => import('./pages/InsightsPage').then(m => ({ default: m.InsightsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));

// ─── Workspace tabs ───
const OverviewTab = lazy(() => import('./pages/workspace/OverviewTab').then(m => ({ default: m.OverviewTab })));
const ArchitectureTab = lazy(() => import('./pages/workspace/ArchitectureTab').then(m => ({ default: m.ArchitectureTab })));
const ChatTab = lazy(() => import('./pages/workspace/ChatTab').then(m => ({ default: m.ChatTab })));
const HealthTab = lazy(() => import('./pages/workspace/HealthTab').then(m => ({ default: m.HealthTab })));
const ReviewsTab = lazy(() => import('./pages/workspace/ReviewsTab').then(m => ({ default: m.ReviewsTab })));
const PullRequestsTab = lazy(() => import('./pages/workspace/PullRequestsTab').then(m => ({ default: m.PullRequestsTab })));
const GitHistoryTab = lazy(() => import('./pages/workspace/GitHistoryTab').then(m => ({ default: m.GitHistoryTab })));
const SettingsTab = lazy(() => import('./pages/workspace/SettingsTab').then(m => ({ default: m.SettingsTab })));

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

/** Lightweight suspense for tab content (no full-page loader) */
function TabSuspense({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-16">
          <div className="h-5 w-5 animate-spin-slow rounded-full border-2 border-brand-500 border-t-transparent" />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

const router = createBrowserRouter([
  // ─── Public routes ───
  { path: '/', element: <SuspenseWrapper><LandingPage /></SuspenseWrapper> },
  { path: '/login', element: <SuspenseWrapper><LoginPage /></SuspenseWrapper> },
  { path: '/signup', element: <SuspenseWrapper><SignupPage /></SuspenseWrapper> },
  { path: '/oauth/callback', element: <SuspenseWrapper><OAuthCallbackPage /></SuspenseWrapper> },

  // ─── Authenticated routes ───
  {
    element: <AuthGuard />,
    children: [
      {
        element: <SuspenseWrapper><AppLayout /></SuspenseWrapper>,
        children: [
          // Dashboard
          { path: '/dashboard', element: <TabSuspense><IntelligenceDashboard /></TabSuspense> },

          // Repositories
          { path: '/repositories', element: <TabSuspense><RepositoriesPage /></TabSuspense> },

          // Repository workspace with tabs
          {
            path: '/repositories/:id',
            element: <TabSuspense><RepositoryWorkspace /></TabSuspense>,
            children: [
              { index: true, element: <TabSuspense><OverviewTab /></TabSuspense> },
              { path: 'architecture', element: <TabSuspense><ArchitectureTab /></TabSuspense> },
              { path: 'chat', element: <TabSuspense><ChatTab /></TabSuspense> },
              { path: 'health', element: <TabSuspense><HealthTab /></TabSuspense> },
              { path: 'reviews', element: <TabSuspense><ReviewsTab /></TabSuspense> },
              { path: 'pulls', element: <TabSuspense><PullRequestsTab /></TabSuspense> },
              { path: 'history', element: <TabSuspense><GitHistoryTab /></TabSuspense> },
              { path: 'settings', element: <TabSuspense><SettingsTab /></TabSuspense> },
            ],
          },

          // Global pages
          { path: '/insights', element: <TabSuspense><InsightsPage /></TabSuspense> },
          { path: '/analytics', element: <TabSuspense><AnalyticsPage /></TabSuspense> },
          { path: '/settings', element: <TabSuspense><SettingsPage /></TabSuspense> },
        ],
      },
    ],
  },

  // ─── Fallback ───
  { path: '*', element: <SuspenseWrapper><NotFoundPage /></SuspenseWrapper> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
