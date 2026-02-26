import { Navigate, Outlet } from "react-router-dom";

/**
 * Route guard that redirects unauthenticated users to /login.
 * Wraps all dashboard routes to prevent unauthorized access.
 */
export default function ProtectedRoute() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
}
