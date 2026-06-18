import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthGuard } from './components/AuthGuard';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { OAuthCallbackPage } from './pages/OAuthCallbackPage';

const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  { path: '/oauth/callback', element: <OAuthCallbackPage /> },
  {
    element: <AuthGuard />,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
