import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "@/features/auth";
import { LoadingScreen } from "@/shared/components/LoadingScreen";

export function ProtectedRoute() {
    const { status, isAuthenticated } = useAuth();
    const location = useLocation();

    if (status === "refreshing" || status === "authenticating" || status === "idle") {
        return <LoadingScreen message="Verifying session..." />;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return <Outlet />;
}
