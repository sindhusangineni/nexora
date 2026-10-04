import { Navigate, Route, Routes } from "react-router-dom";

import { AdminLayout } from "@/app/layouts/AdminLayout";
import { PublicLayout } from "@/app/layouts/PublicLayout";
import { StudentLayout } from "@/app/layouts/StudentLayout";
import { ProtectedRoute } from "@/app/router/guards/ProtectedRoute";
import { PublicRoute } from "@/app/router/guards/PublicRoute";
import { RoleRoute } from "@/app/router/guards/RoleRoute";
import { AdminAssessmentsPage } from "@/pages/admin/AdminAssessmentsPage";
import { AdminAssessmentCreatePage } from "@/pages/admin/AdminAssessmentCreatePage";
import { AdminAssessmentDetailPage } from "@/pages/admin/AdminAssessmentDetailPage";
import { AdminAssessmentEditPage } from "@/pages/admin/AdminAssessmentEditPage";
import { AdminAssessmentPaperPage } from "@/pages/admin/AdminAssessmentPaperPage";
import { AdminDashboardPage } from "@/pages/admin/AdminDashboardPage";
import { AdminLearningPage } from "@/pages/admin/AdminLearningPage";
import { AdminQuestionBankPage } from "@/pages/admin/AdminQuestionBankPage";
import { AdminQuestionCreatePage } from "@/pages/admin/AdminQuestionCreatePage";
import { AdminQuestionDetailPage } from "@/pages/admin/AdminQuestionDetailPage";
import { AdminQuestionEditPage } from "@/pages/admin/AdminQuestionEditPage";
import { AdminQuestionImportPage } from "@/pages/admin/AdminQuestionImportPage";
import { LoginPage } from "@/pages/auth/LoginPage";
import { SignupPage } from "@/pages/auth/SignupPage";
import { NotFoundPage } from "@/pages/common/NotFoundPage";
import { PlaceholderPage } from "@/pages/common/PlaceholderPage";
import { LandingPage } from "@/pages/public/LandingPage";
import { StudentAssessmentsPage } from "@/pages/student/StudentAssessmentsPage";
import { StudentAttemptsPage } from "@/pages/student/StudentAttemptsPage";
import { StudentAttemptWorkspacePage } from "@/pages/student/StudentAttemptWorkspacePage";
import { StudentAttemptResultPage } from "@/pages/student/StudentAttemptResultPage";
import { AdminAttemptReviewPage } from "@/pages/admin/AdminAttemptReviewPage";
import { StudentDashboardPage } from "@/pages/student/StudentDashboardPage";
import { StudentLearningPage } from "@/pages/student/StudentLearningPage";

export function AppRoutes() {
    return (
        <Routes>
            {/* Public Landing Page */}
            <Route path="/" element={<LandingPage />} />

            {/* Public / Auth routes (accessible when not authenticated) */}
            <Route element={<PublicRoute />}>
                <Route element={<PublicLayout />}>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/signup" element={<SignupPage />} />
                </Route>
            </Route>

            {/* Student routes */}
            <Route element={<ProtectedRoute />}>
                <Route element={<RoleRoute allowedRoles={["student"]} />}>
                    {/* Distraction-free active attempt workspace */}
                    <Route
                        path="/student/attempts/:attemptId"
                        element={<StudentAttemptWorkspacePage />}
                    />

                    <Route path="/student" element={<StudentLayout />}>
                        <Route index element={<Navigate to="/student/dashboard" replace />} />
                        <Route path="dashboard" element={<StudentDashboardPage />} />
                        <Route path="learning" element={<StudentLearningPage />} />
                        <Route
                            path="assessments"
                            element={<StudentAssessmentsPage />}
                        />
                        <Route
                            path="attempts"
                            element={<StudentAttemptsPage />}
                        />
                        <Route
                            path="attempts/:attemptId/result"
                            element={<StudentAttemptResultPage />}
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
                        <Route path="learning" element={<AdminLearningPage />} />
                        <Route path="question-bank" element={<AdminQuestionBankPage />} />
                        <Route
                            path="question-bank/questions"
                            element={<AdminQuestionBankPage />}
                        />
                        <Route
                            path="question-bank/questions/new"
                            element={<AdminQuestionCreatePage />}
                        />
                        <Route
                            path="question-bank/import"
                            element={<AdminQuestionImportPage />}
                        />
                        <Route
                            path="question-bank/create"
                            element={<AdminQuestionCreatePage />}
                        />
                        <Route
                            path="question-bank/questions/:questionId"
                            element={<AdminQuestionDetailPage />}
                        />
                        <Route
                            path="question-bank/questions/:questionId/edit"
                            element={<AdminQuestionEditPage />}
                        />
                        <Route
                            path="question-bank/questions/:questionId/versions"
                            element={<AdminQuestionDetailPage />}
                        />
                        <Route
                            path="assessments"
                            element={<AdminAssessmentsPage />}
                        />
                        <Route
                            path="assessments/new"
                            element={<AdminAssessmentCreatePage />}
                        />
                        <Route
                            path="assessments/:assessmentId"
                            element={<AdminAssessmentDetailPage />}
                        />
                        <Route
                            path="assessments/:assessmentId/edit"
                            element={<AdminAssessmentEditPage />}
                        />
                        <Route
                            path="assessments/:assessmentId/paper"
                            element={<AdminAssessmentPaperPage />}
                        />
                        <Route
                            path="attempts"
                            element={<PlaceholderPage title="Attempts & Descriptive Grading" />}
                        />
                        <Route
                            path="attempts/:attemptId"
                            element={<AdminAttemptReviewPage />}
                        />
                    </Route>
                </Route>
            </Route>

            {/* 404 Catch-all */}
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    );
}
