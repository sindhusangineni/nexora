import { Navigate, Route, Routes } from "react-router-dom";

import { AdminLayout } from "@/app/layouts/AdminLayout";
import { PublicLayout } from "@/app/layouts/PublicLayout";
import { StudentLayout } from "@/app/layouts/StudentLayout";
import { ProtectedRoute } from "@/app/router/guards/ProtectedRoute";
import { PublicRoute } from "@/app/router/guards/PublicRoute";
import { RoleRoute } from "@/app/router/guards/RoleRoute";
import { AdminDashboardPage } from "@/pages/admin/AdminDashboardPage";
import { LoginPage } from "@/pages/auth/LoginPage";
import { NotFoundPage } from "@/pages/common/NotFoundPage";
import { PlaceholderPage } from "@/pages/common/PlaceholderPage";
import { StudentDashboardPage } from "@/pages/student/StudentDashboardPage";

export function AppRoutes() {
    return (
        <Routes>
            {/* Public / Auth routes */}
            <Route element={<PublicRoute />}>
                <Route element={<PublicLayout />}>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/" element={<Navigate to="/login" replace />} />
                </Route>
            </Route>

            {/* Student routes */}
            <Route element={<ProtectedRoute />}>
                <Route element={<RoleRoute allowedRoles={["student"]} />}>
                    <Route path="/student" element={<StudentLayout />}>
                        <Route index element={<Navigate to="/student/dashboard" replace />} />
                        <Route path="dashboard" element={<StudentDashboardPage />} />
                        <Route
                            path="learning"
                            element={<PlaceholderPage title="Curriculum & Learning" />}
                        />
                        <Route
                            path="assessments"
                            element={<PlaceholderPage title="Available Assessments" />}
                        />
                        <Route
                            path="attempts"
                            element={<PlaceholderPage title="My Attempts & Scorecards" />}
                        />
                    </Route>
                </Route>
            </Route>

            {/* Admin routes */}
            <Route element={<ProtectedRoute />}>
                <Route element={<RoleRoute allowedRoles={["superadmin"]} />}>
                    <Route path="/admin" element={<AdminLayout />}>
                        <Route index element={<Navigate to="/admin/dashboard" replace />} />
                        <Route path="dashboard" element={<AdminDashboardPage />} />
                        <Route
                            path="learning"
                            element={<PlaceholderPage title="Learning Taxonomy Management" />}
                        />
                        <Route
                            path="question-bank"
                            element={<PlaceholderPage title="Question Bank Administration" />}
                        />
                        <Route
                            path="assessments"
                            element={<PlaceholderPage title="Assessment Configuration" />}
                        />
                        <Route
                            path="attempts"
                            element={<PlaceholderPage title="Attempts & Descriptive Grading" />}
                        />
                    </Route>
                </Route>
            </Route>

            {/* 404 Catch-all */}
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    );
}
