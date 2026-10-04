import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AdminAssessmentsPage } from "@/pages/admin/AdminAssessmentsPage";
import { AdminAssessmentCreatePage } from "@/pages/admin/AdminAssessmentCreatePage";
import { AdminAssessmentDetailPage } from "@/pages/admin/AdminAssessmentDetailPage";
import { AdminAssessmentEditPage } from "@/pages/admin/AdminAssessmentEditPage";
import { AdminAssessmentPaperPage } from "@/pages/admin/AdminAssessmentPaperPage";
import { StudentAssessmentsPage } from "@/pages/student/StudentAssessmentsPage";
import { assessmentApi } from "../api/assessmentApi";
import type { Assessment, AssessmentPaper } from "../types/assessment.types";

function renderWithRouter(
    ui: React.ReactElement,
    initialRoute: string = "/",
    routes?: { path: string; element: React.ReactElement }[],
) {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });

    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={[initialRoute]}>
                {routes ? (
                    <Routes>
                        <Route path={initialRoute} element={ui} />
                        {routes.map((r) => (
                            <Route key={r.path} path={r.path} element={r.element} />
                        ))}
                    </Routes>
                ) : (
                    ui
                )}
            </MemoryRouter>
        </QueryClientProvider>,
    );
}

describe("Assessment Pages", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    const dummyDraftAssessment: Assessment = {
        id: "asm-1",
        title: "Polity Mock Examination",
        description: "Comprehensive test covering Indian Constitution",
        type: "MOCK",
        status: "DRAFT",
        duration_seconds: 7200,
        marks_per_question: "2.00",
        penalty_per_question: "0.66",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
    };

    const dummyPublishedAssessment: Assessment = {
        id: "asm-2",
        title: "History Practice Set",
        description: "Ancient and Medieval History",
        type: "PRACTICE",
        status: "PUBLISHED",
        duration_seconds: 3600,
        marks_per_question: "2.00",
        penalty_per_question: "0.00",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
    };

    describe("AdminAssessmentsPage", () => {
        it("renders assessments list, search filter, and status filter", async () => {
            const user = userEvent.setup();
            vi.spyOn(assessmentApi, "listAssessments").mockResolvedValueOnce([
                dummyDraftAssessment,
                dummyPublishedAssessment,
            ]);

            renderWithRouter(<AdminAssessmentsPage />, "/admin/assessments");

            await waitFor(() => {
                expect(screen.getByText("Polity Mock Examination")).toBeInTheDocument();
                expect(screen.getByText("History Practice Set")).toBeInTheDocument();
            });

            // Filter by search
            const searchInput = screen.getByLabelText(/search assessments/i);
            await user.type(searchInput, "Polity");

            expect(screen.getByText("Polity Mock Examination")).toBeInTheDocument();
            expect(screen.queryByText("History Practice Set")).not.toBeInTheDocument();
        });
    });

    describe("AdminAssessmentCreatePage", () => {
        it("renders wizard step 1 and navigates to step 2", async () => {
            const user = userEvent.setup();
            renderWithRouter(
                <AdminAssessmentCreatePage />,
                "/admin/assessments/new",
            );

            expect(screen.getByRole("heading", { name: /create new assessment/i })).toBeInTheDocument();
            expect(screen.getByLabelText(/assessment title/i)).toBeInTheDocument();

            const titleInput = screen.getByLabelText(/assessment title/i);
            await user.type(titleInput, "Environment Practice Test");

            const nextBtn = screen.getByRole("button", { name: /continue to timing/i });
            await user.click(nextBtn);

            expect(screen.getByText(/timing, marks & scoring policy/i)).toBeInTheDocument();
        });
    });

    describe("AdminAssessmentDetailPage", () => {
        it("renders assessment details and review information", async () => {
            vi.spyOn(assessmentApi, "getAssessment").mockResolvedValueOnce(
                dummyDraftAssessment,
            );
            vi.spyOn(assessmentApi, "listSections").mockResolvedValueOnce([]);
            vi.spyOn(assessmentApi, "listRules").mockResolvedValueOnce([]);

            renderWithRouter(
                <Routes>
                    <Route
                        path="/admin/assessments/:assessmentId"
                        element={<AdminAssessmentDetailPage />}
                    />
                </Routes>,
                "/admin/assessments/asm-1",
            );

            await waitFor(() => {
                expect(
                    screen.getByRole("heading", {
                        level: 1,
                        name: "Polity Mock Examination",
                    }),
                ).toBeInTheDocument();
            });

            expect(screen.getByText("120 mins")).toBeInTheDocument();
            expect(
                screen.getAllByText("+2.00 / -0.66").length,
            ).toBeGreaterThan(0);
            expect(screen.getByRole("button", { name: /edit builder/i })).toBeInTheDocument();
        });
    });

    describe("AdminAssessmentEditPage", () => {
        it("renders builder tabs and updates assessment details", async () => {
            const user = userEvent.setup();
            vi.spyOn(assessmentApi, "getAssessment").mockResolvedValueOnce(
                dummyDraftAssessment,
            );
            vi.spyOn(assessmentApi, "listSections").mockResolvedValueOnce([]);
            vi.spyOn(assessmentApi, "listRules").mockResolvedValueOnce([]);
            const updateSpy = vi
                .spyOn(assessmentApi, "updateAssessment")
                .mockResolvedValueOnce({
                    ...dummyDraftAssessment,
                    title: "Polity Mock Updated",
                });

            renderWithRouter(
                <Routes>
                    <Route
                        path="/admin/assessments/:assessmentId/edit"
                        element={<AdminAssessmentEditPage />}
                    />
                </Routes>,
                "/admin/assessments/asm-1/edit",
            );

            await waitFor(() => {
                expect(screen.getByDisplayValue("Polity Mock Examination")).toBeInTheDocument();
            });

            const titleInput = screen.getByDisplayValue("Polity Mock Examination");
            await user.clear(titleInput);
            await user.type(titleInput, "Polity Mock Updated");

            const saveBtn = screen.getByRole("button", { name: /save details/i });
            await user.click(saveBtn);

            expect(updateSpy).toHaveBeenCalledWith("asm-1", expect.objectContaining({
                title: "Polity Mock Updated",
            }));
        });

        it("displays immutable banner if assessment is published", async () => {
            vi.spyOn(assessmentApi, "getAssessment").mockResolvedValueOnce(
                dummyPublishedAssessment,
            );
            vi.spyOn(assessmentApi, "listSections").mockResolvedValueOnce([]);
            vi.spyOn(assessmentApi, "listRules").mockResolvedValueOnce([]);

            renderWithRouter(
                <Routes>
                    <Route
                        path="/admin/assessments/:assessmentId/edit"
                        element={<AdminAssessmentEditPage />}
                    />
                </Routes>,
                "/admin/assessments/asm-2/edit",
            );

            await waitFor(() => {
                expect(
                    screen.getByText(/assessment is immutable/i),
                ).toBeInTheDocument();
            });
        });
    });

    describe("AdminAssessmentPaperPage", () => {
        const dummyPaper: AssessmentPaper = {
            id: "paper-1",
            assessment_id: "asm-2",
            status: "GENERATED",
            duration_seconds: 3600,
            marks_per_question: "2.00",
            penalty_per_question: "0.00",
            created_at: new Date().toISOString(),
            items: [
                {
                    id: "pi-1",
                    paper_id: "paper-1",
                    question_id: "q-1",
                    question_version_id: "qv-1",
                    assessment_section_id: null,
                    presentation_order: 1,
                    allocated_marks: "2.00",
                    allocated_penalty: "0.00",
                    created_at: new Date().toISOString(),
                },
            ],
        };

        it("loads and displays generated paper artifact", async () => {
            vi.spyOn(assessmentApi, "getAssessment").mockResolvedValueOnce(
                dummyPublishedAssessment,
            );
            vi.spyOn(assessmentApi, "listSections").mockResolvedValueOnce([]);
            vi.spyOn(assessmentApi, "getPaper").mockResolvedValueOnce(dummyPaper);

            renderWithRouter(
                <Routes>
                    <Route
                        path="/admin/assessments/:assessmentId/paper"
                        element={<AdminAssessmentPaperPage />}
                    />
                </Routes>,
                "/admin/assessments/asm-2/paper?paperId=paper-1",
            );

            await waitFor(() => {
                expect(
                    screen.getByRole("heading", {
                        name: /immutable test paper artifact/i,
                    }),
                ).toBeInTheDocument();
            });

            expect(
                screen.getByRole("heading", { level: 2, name: "History Practice Set" }),
            ).toBeInTheDocument();
            expect(screen.getByText("q-1")).toBeInTheDocument();
            expect(screen.getByText("qv-1")).toBeInTheDocument();
        });
    });

    describe("StudentAssessmentsPage", () => {
        it("displays published assessments for student with Phase 3D note", async () => {
            vi.spyOn(assessmentApi, "listAssessments").mockResolvedValueOnce([
                dummyPublishedAssessment,
            ]);

            renderWithRouter(<StudentAssessmentsPage />, "/student/assessments");

            await waitFor(() => {
                expect(screen.getByText("History Practice Set")).toBeInTheDocument();
            });

            expect(
                screen.getByText(/attempts will be enabled in phase 3d/i),
            ).toBeInTheDocument();
        });
    });
});
