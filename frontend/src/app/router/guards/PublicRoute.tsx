import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/features/auth";
import { LoadingScreen } from "@/shared/components/LoadingScreen";

export function PublicRoute() {
    const { status, isAuthenticated, isSuperadmin } = useAuth();

    if (status === "refreshing" || status === "authenticating" || status === "idle") {
        return <LoadingScreen message="Checking session..." />;
    }

    if (isAuthenticated) {
        return (
            <Navigate
                to={isSuperadmin ? "/admin/dashboard" : "/student/dashboard"}
                replace
            />
        );
    }

    return <Outlet />;
}
