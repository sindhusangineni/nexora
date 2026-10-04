import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/features/auth";

export interface RoleRouteProps {
    allowedRoles: string[];
}

export function RoleRoute({ allowedRoles }: RoleRouteProps) {
    const { user, isSuperadmin, isStudent } = useAuth();

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    const normalizedAllowed = allowedRoles.map((r) => r.toLowerCase());
    const hasRole = user.roles.some((role) =>
        normalizedAllowed.includes(role.toLowerCase()),
    );

    if (!hasRole) {
        // Redirect unauthorized user to their respective home
        if (isSuperadmin) {
            return <Navigate to="/admin/dashboard" replace />;
        }
        if (isStudent) {
            return <Navigate to="/student/dashboard" replace />;
        }
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
}
