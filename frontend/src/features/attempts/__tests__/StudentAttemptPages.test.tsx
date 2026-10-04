import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StudentAttemptsPage } from "@/pages/student/StudentAttemptsPage";
import { StudentAttemptResultPage } from "@/pages/student/StudentAttemptResultPage";
import { StudentAssessmentsPage } from "@/pages/student/StudentAssessmentsPage";
import { attemptsApi } from "../api/attemptsApi";
import { assessmentApi } from "@/features/assessment/api/assessmentApi";

vi.mock("../api/attemptsApi", () => ({
    attemptsApi: {
        getAttempt: vi.fn(),
        getAttemptResult: vi.fn(),
        getAttemptReview: vi.fn(),
        getAssessmentPaper: vi.fn(),
        getAssessment: vi.fn(),
        startAttempt: vi.fn(),
        getAttemptHistory: vi.fn(),
    },
}));

vi.mock("@/features/assessment/api/assessmentApi", () => ({
    assessmentApi: {
        listAssessments: vi.fn(),
        generatePaper: vi.fn(),
    },
}));

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
}

describe("Student Attempt Pages", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(attemptsApi.getAssessmentPaper).mockResolvedValue({
            id: "paper-1",
            assessment_id: "asm-1",
            status: "GENERATED",
            duration_seconds: 3600,
            marks_per_question: "2.00",
            penalty_per_question: "0.50",
            created_at: "",
            items: [],
        });
        vi.mocked(attemptsApi.getAssessment).mockResolvedValue({
            id: "asm-1",
            title: "UPSC Prelims Mock 01",
            description: "",
            type: "MOCK",
            status: "PUBLISHED",
            duration_seconds: 3600,
            marks_per_question: "2.00",
            penalty_per_question: "0.50",
            created_at: "",
            updated_at: "",
        });
    });

    describe("StudentAttemptsPage", () => {
        it("renders empty history state when no attempts exist", async () => {
            vi.mocked(attemptsApi.getAttemptHistory).mockResolvedValueOnce({
                count: 0,
                next: null,
                previous: null,
                results: [],
            });

            render(
                <MemoryRouter>
                    <StudentAttemptsPage />
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            expect(screen.getByText("My Attempts")).toBeInTheDocument();
            expect(screen.getByPlaceholderText(/Enter Attempt UUID/i)).toBeInTheDocument();
            expect(screen.getByText("Take New Assessment")).toBeInTheDocument();

            await waitFor(() => {
                expect(screen.getByText("No Attempts Yet")).toBeInTheDocument();
            });
            expect(
                screen.getByText(/Your attempt history will appear here once you take your first test./i),
            ).toBeInTheDocument();
        });

        it("renders attempt history with status, score, timeline, and actions", async () => {
            const mockHistory = {
                count: 4,
                next: null,
                previous: null,
                results: [
                    {
                        id: "att-1",
                        assessment_paper_id: "paper-1111-2222",
                        attempt_number: 1,
                        status: "IN_PROGRESS" as const,
                        started_at: "2026-10-04T00:00:00Z",
                        submitted_at: null,
                        expires_at: "2026-10-04T01:00:00Z",
                        submission_reason: null,
                        result_status: null,
                        score: null,
                        maximum_score: null,
                        percentage: null,
                        total_questions: null,
                        attempted_questions: null,
                    },
                    {
                        id: "att-2",
                        assessment_paper_id: "paper-2222-3333",
                        attempt_number: 2,
                        status: "SUBMITTED" as const,
                        started_at: "2026-10-03T10:00:00Z",
                        submitted_at: "2026-10-03T10:45:00Z",
                        expires_at: "2026-10-03T11:00:00Z",
                        submission_reason: "MANUAL" as const,
                        result_status: "PENDING" as const,
                        score: null,
                        maximum_score: null,
                        percentage: null,
                        total_questions: 10,
                        attempted_questions: 8,
                    },
                    {
                        id: "att-3",
                        assessment_paper_id: "paper-3333-4444",
                        attempt_number: 3,
                        status: "EVALUATED" as const,
                        started_at: "2026-10-02T10:00:00Z",
                        submitted_at: "2026-10-02T10:50:00Z",
                        expires_at: "2026-10-02T11:00:00Z",
                        submission_reason: "MANUAL" as const,
                        result_status: "FINAL" as const,
                        score: "85.00",
                        maximum_score: "100.00",
                        percentage: "85.00",
                        total_questions: 50,
                        attempted_questions: 48,
                    },
                    {
                        id: "att-4",
                        assessment_paper_id: "paper-4444-5555",
                        attempt_number: 4,
                        status: "CANCELLED" as const,
                        started_at: "2026-10-01T10:00:00Z",
                        submitted_at: null,
                        expires_at: "2026-10-01T11:00:00Z",
                        submission_reason: null,
                        result_status: "VOID" as const,
                        score: null,
                        maximum_score: null,
                        percentage: null,
                        total_questions: null,
                        attempted_questions: null,
                    },
                ],
            };
            vi.mocked(attemptsApi.getAttemptHistory).mockResolvedValueOnce(mockHistory);

            render(
                <MemoryRouter>
                    <StudentAttemptsPage />
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            await waitFor(() => {
                expect(screen.getAllByText("Attempt #1").length).toBeGreaterThanOrEqual(1);
            });

            expect(screen.getAllByText("Attempt #2").length).toBeGreaterThanOrEqual(1);
            expect(screen.getAllByText("Attempt #3").length).toBeGreaterThanOrEqual(1);
            expect(screen.getAllByText("Attempt #4").length).toBeGreaterThanOrEqual(1);

            // Status badges
            const table = screen.getByRole("table");
            expect(within(table).getByText("In Progress")).toBeInTheDocument();
            expect(within(table).getByText("Submitted")).toBeInTheDocument();
            expect(within(table).getByText("Evaluated")).toBeInTheDocument();
            expect(within(table).getByText("Cancelled")).toBeInTheDocument();

            // Results within table
            expect(within(table).getByText("Pending Evaluation")).toBeInTheDocument();
            expect(within(table).getByText("85.00 / 100.00")).toBeInTheDocument();
            expect(within(table).getByText("85.00%")).toBeInTheDocument();
            expect(within(table).getByText("Void")).toBeInTheDocument();

            // Action buttons
            expect(screen.getAllByRole("button", { name: "Continue Test" }).length).toBeGreaterThanOrEqual(1);
            expect(screen.getAllByRole("button", { name: "View Result" }).length).toBeGreaterThanOrEqual(2);
            expect(screen.getAllByRole("button", { name: "Details" }).length).toBeGreaterThanOrEqual(1);
        });

        it("handles filter changes and direct attempt lookup", async () => {
            vi.mocked(attemptsApi.getAttemptHistory).mockResolvedValue({
                count: 0,
                next: null,
                previous: null,
                results: [],
            });

            render(
                <MemoryRouter initialEntries={["/student/attempts"]}>
                    <Routes>
                        <Route path="/student/attempts" element={<StudentAttemptsPage />} />
                        <Route
                            path="/student/attempts/:id"
                            element={<div data-testid="attempt-workspace">Workspace</div>}
                        />
                    </Routes>
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            // Filter selection
            const filterSelect = screen.getByLabelText(/Filter by Status/i);
            fireEvent.change(filterSelect, { target: { value: "IN_PROGRESS" } });

            await waitFor(() => {
                expect(attemptsApi.getAttemptHistory).toHaveBeenCalledWith({
                    status: "IN_PROGRESS",
                    page: 1,
                    page_size: 20,
                });
            });

            // Direct attempt lookup form
            const input = screen.getByPlaceholderText(/Enter Attempt UUID/i);
            const submitBtn = screen.getByRole("button", { name: "Go to Attempt" });

            fireEvent.change(input, { target: { value: "11111111-2222-3333-4444-555555555555" } });
            fireEvent.click(submitBtn);

            await waitFor(() => {
                expect(screen.getByTestId("attempt-workspace")).toBeInTheDocument();
            });
        });

        it("renders pagination controls when multiple pages exist", async () => {
            vi.mocked(attemptsApi.getAttemptHistory).mockResolvedValue({
                count: 35,
                next: "/attempts/?page=2",
                previous: null,
                results: [
                    {
                        id: "att-1",
                        assessment_paper_id: "paper-1",
                        attempt_number: 1,
                        status: "IN_PROGRESS" as const,
                        started_at: "2026-10-04T00:00:00Z",
                        submitted_at: null,
                        expires_at: "2026-10-04T01:00:00Z",
                        submission_reason: null,
                        result_status: null,
                        score: null,
                        maximum_score: null,
                        percentage: null,
                        total_questions: null,
                        attempted_questions: null,
                    },
                ],
            });

            render(
                <MemoryRouter>
                    <StudentAttemptsPage />
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            await waitFor(() => {
                expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();
            });

            const nextBtn = screen.getByRole("button", { name: "Next" });
            expect(nextBtn).toBeEnabled();
            const prevBtn = screen.getByRole("button", { name: "Previous" });
            expect(prevBtn).toBeDisabled();

            fireEvent.click(nextBtn);
            await waitFor(() => {
                expect(attemptsApi.getAttemptHistory).toHaveBeenCalledWith({
                    status: undefined,
                    page: 2,
                    page_size: 20,
                });
            });
        });
    });

    describe("StudentAttemptResultPage", () => {
        it("renders final scorecard, section breakdown, and review list", async () => {
            vi.mocked(attemptsApi.getAttemptReview).mockResolvedValueOnce({
                id: "att-1",
                student_id: "stu-1",
                assessment_paper_id: "paper-1",
                attempt_number: 1,
                duration_seconds: 3600,
                started_at: "2026-10-04T00:00:00Z",
                submitted_at: "2026-10-04T00:45:00Z",
                submission_reason: "MANUAL",
                status: "EVALUATED",
                result_status: "FINAL",
                items: [
                    {
                        id: "item-1",
                        paper_item_id: "pi-1",
                        assessment_section_id: "sec-1",
                        section_name: "Polity & Constitution",
                        question_id: "q-1",
                        question_version_id: "qv-1",
                        question_number: 1,
                        presentation_order: 1,
                        question_type: "MCQ",
                        question_text: "Which Article guarantees the Right to Equality?",
                        allocated_marks: "2.00",
                        allocated_penalty: "0.50",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "CORRECT",
                        marks_awarded: "2.00",
                        explanation: "Article 14 guarantees equality before the law.",
                        choices: [
                            { id: "c-1", text: "Article 14", position: 1, is_correct: true },
                            { id: "c-2", text: "Article 21", position: 2, is_correct: false },
                        ],
                        candidate_answer: { selected_choice_id: "c-1" },
                        correct_answer: { correct_choice_id: "c-1" },
                    },
                ],
                result: {
                    id: "res-1",
                    attempt_id: "att-1",
                    status: "FINAL",
                    score: "85.00",
                    maximum_score: "100.00",
                    percentage: "85.00",
                    total_questions: 1,
                    attempted_questions: 1,
                    correct_questions: 1,
                    incorrect_questions: 0,
                    partially_correct_questions: 0,
                    unanswered_questions: 0,
                    pending_evaluation_questions: 0,
                    finalized_at: "2026-10-04T00:45:01Z",
                    section_results: [
                        {
                            id: "sres-1",
                            assessment_section_id: "sec-1",
                            section_title_snapshot: "Polity & Constitution",
                            section_order_snapshot: 1,
                            score: "40.00",
                            maximum_score: "50.00",
                            percentage: "80.00",
                            attempted_questions: 1,
                            correct_questions: 1,
                            incorrect_questions: 0,
                            partially_correct_questions: 0,
                            unanswered_questions: 0,
                            pending_evaluation_questions: 0,
                        },
                    ],
                },
            });

            vi.mocked(attemptsApi.getAssessmentPaper).mockResolvedValueOnce({
                id: "paper-1",
                assessment_id: "asm-1",
                status: "GENERATED",
                duration_seconds: 3600,
                marks_per_question: "2.00",
                penalty_per_question: "0.50",
                created_at: "",
                items: [],
            });

            vi.mocked(attemptsApi.getAssessment).mockResolvedValueOnce({
                id: "asm-1",
                title: "UPSC Prelims Mock 01",
                description: "",
                type: "MOCK",
                status: "PUBLISHED",
                duration_seconds: 3600,
                marks_per_question: "2.00",
                penalty_per_question: "0.50",
                created_at: "",
                updated_at: "",
            });

            render(
                <MemoryRouter initialEntries={["/student/attempts/att-1/result"]}>
                    <Routes>
                        <Route
                            path="/student/attempts/:attemptId/result"
                            element={<StudentAttemptResultPage />}
                        />
                    </Routes>
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            await waitFor(() => {
                expect(screen.getByText("UPSC Prelims Mock 01")).toBeInTheDocument();
                expect(screen.getAllByText(/85.00/i)[0]).toBeInTheDocument();
                expect(screen.getAllByText("Polity & Constitution")[0]).toBeInTheDocument();
                expect(screen.getByText("Which Article guarantees the Right to Equality?")).toBeInTheDocument();
                expect(screen.getByText("Article 14 guarantees equality before the law.")).toBeInTheDocument();
            });
        });

        it("renders pending descriptive evaluation state with solutions withheld", async () => {
            vi.mocked(attemptsApi.getAttemptReview).mockResolvedValueOnce({
                id: "att-1",
                student_id: "stu-1",
                assessment_paper_id: "paper-1",
                attempt_number: 1,
                duration_seconds: 3600,
                started_at: "2026-10-04T00:00:00Z",
                submitted_at: "2026-10-04T00:45:00Z",
                submission_reason: "MANUAL",
                status: "SUBMITTED",
                result_status: "PENDING",
                items: [
                    {
                        id: "item-desc",
                        paper_item_id: "pi-desc",
                        assessment_section_id: "sec-1",
                        section_name: "Essay Section",
                        question_id: "q-desc",
                        question_version_id: "qv-desc",
                        question_number: 1,
                        presentation_order: 1,
                        question_type: "DESCRIPTIVE",
                        question_text: "Discuss the key features of the Basic Structure doctrine.",
                        allocated_marks: "10.00",
                        allocated_penalty: "0.00",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "PENDING_EVALUATION",
                        marks_awarded: null,
                        explanation: null,
                        candidate_answer: { text_response: "The basic structure doctrine was established in Kesavananda Bharati case." },
                        correct_answer: null,
                    },
                ],
                result: {
                    id: "res-1",
                    attempt_id: "att-1",
                    status: "PENDING",
                    score: "0.00",
                    maximum_score: "10.00",
                    percentage: "0.00",
                    total_questions: 1,
                    attempted_questions: 1,
                    correct_questions: 0,
                    incorrect_questions: 0,
                    partially_correct_questions: 0,
                    unanswered_questions: 0,
                    pending_evaluation_questions: 1,
                    finalized_at: null,
                    section_results: [],
                },
            });

            render(
                <MemoryRouter initialEntries={["/student/attempts/att-1/result"]}>
                    <Routes>
                        <Route
                            path="/student/attempts/:attemptId/result"
                            element={<StudentAttemptResultPage />}
                        />
                    </Routes>
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            await waitFor(() => {
                expect(screen.getByText(/Pending Descriptive Review/i)).toBeInTheDocument();
                expect(screen.getByText(/Detailed solutions and explanations will be unlocked once manual evaluation is finalized/i)).toBeInTheDocument();
                expect(screen.getByText("The basic structure doctrine was established in Kesavananda Bharati case.")).toBeInTheDocument();
            });
        });

        it("renders all 6 question types and supports filtering", async () => {
            vi.mocked(attemptsApi.getAttemptReview).mockResolvedValueOnce({
                id: "att-all",
                student_id: "stu-1",
                assessment_paper_id: "paper-1",
                attempt_number: 1,
                duration_seconds: 3600,
                started_at: "2026-10-04T00:00:00Z",
                submitted_at: "2026-10-04T00:45:00Z",
                submission_reason: "MANUAL",
                status: "EVALUATED",
                result_status: "FINAL",
                items: [
                    {
                        id: "it-mcq",
                        paper_item_id: "pi-1",
                        assessment_section_id: "sec-1",
                        section_name: "Mixed Section",
                        question_id: "q-1",
                        question_version_id: "qv-1",
                        question_number: 1,
                        presentation_order: 1,
                        question_type: "MCQ",
                        question_text: "MCQ Question Text",
                        allocated_marks: "2.00",
                        allocated_penalty: "0.50",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "CORRECT",
                        marks_awarded: "2.00",
                        explanation: "MCQ Explanation Text",
                        choices: [
                            { id: "c1", text: "Option A", position: 1, is_correct: true },
                            { id: "c2", text: "Option B", position: 2, is_correct: false },
                        ],
                        candidate_answer: { selected_choice_id: "c1" },
                        correct_answer: { correct_choice_id: "c1" },
                    },
                    {
                        id: "it-ms",
                        paper_item_id: "pi-2",
                        assessment_section_id: "sec-1",
                        section_name: "Mixed Section",
                        question_id: "q-2",
                        question_version_id: "qv-2",
                        question_number: 2,
                        presentation_order: 2,
                        question_type: "MULTIPLE_SELECT",
                        question_text: "Multiple Select Question Text",
                        allocated_marks: "4.00",
                        allocated_penalty: "1.00",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "INCORRECT",
                        marks_awarded: "0.00",
                        explanation: "MS Explanation",
                        choices: [
                            { id: "ms1", text: "MS Option 1", position: 1, is_correct: true },
                            { id: "ms2", text: "MS Option 2", position: 2, is_correct: true },
                        ],
                        candidate_answer: { selected_choice_ids: ["ms1"] },
                        correct_answer: { correct_choice_ids: ["ms1", "ms2"] },
                    },
                    {
                        id: "it-tf",
                        paper_item_id: "pi-3",
                        assessment_section_id: "sec-1",
                        section_name: "Mixed Section",
                        question_id: "q-3",
                        question_version_id: "qv-3",
                        question_number: 3,
                        presentation_order: 3,
                        question_type: "TRUE_FALSE",
                        question_text: "True False Question Text",
                        allocated_marks: "1.00",
                        allocated_penalty: "0.00",
                        is_answered: false,
                        answer_state: "UNANSWERED",
                        evaluation_status: "UNATTEMPTED",
                        marks_awarded: "0.00",
                        explanation: "TF Explanation",
                        candidate_answer: { boolean_response: null },
                        correct_answer: { correct_boolean: true },
                    },
                    {
                        id: "it-ar",
                        paper_item_id: "pi-4",
                        assessment_section_id: "sec-1",
                        section_name: "Mixed Section",
                        question_id: "q-4",
                        question_version_id: "qv-4",
                        question_number: 4,
                        presentation_order: 4,
                        question_type: "ASSERTION_REASON",
                        question_text: "AR Question Text",
                        assertion: "Assertion statement text",
                        reason: "Reason statement text",
                        allocated_marks: "2.00",
                        allocated_penalty: "0.50",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "CORRECT",
                        marks_awarded: "2.00",
                        explanation: "AR Explanation",
                        candidate_answer: { assertion_reason_response: "ASSERTION_TRUE_REASON_FALSE" },
                        correct_answer: { correct_relationship: "ASSERTION_TRUE_REASON_FALSE" },
                    },
                    {
                        id: "it-mf",
                        paper_item_id: "pi-5",
                        assessment_section_id: "sec-1",
                        section_name: "Mixed Section",
                        question_id: "q-5",
                        question_version_id: "qv-5",
                        question_number: 5,
                        presentation_order: 5,
                        question_type: "MATCH_FOLLOWING",
                        question_text: "Match Following Question Text",
                        allocated_marks: "3.00",
                        allocated_penalty: "0.00",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "CORRECT",
                        marks_awarded: "3.00",
                        explanation: "MF Explanation",
                        left_items: [{ id: "l1", text: "Left Item 1", position: 1 }],
                        right_items: [{ id: "r1", text: "Right Item 1", position: 1 }],
                        candidate_answer: { matches: [{ left_item_id: "l1", right_item_id: "r1" }] },
                        correct_answer: { correct_matches: [{ left_item_id: "l1", right_item_id: "r1" }] },
                    },
                    {
                        id: "it-desc",
                        paper_item_id: "pi-6",
                        assessment_section_id: "sec-1",
                        section_name: "Mixed Section",
                        question_id: "q-6",
                        question_version_id: "qv-6",
                        question_number: 6,
                        presentation_order: 6,
                        question_type: "DESCRIPTIVE",
                        question_text: "Descriptive Question Text",
                        allocated_marks: "10.00",
                        allocated_penalty: "0.00",
                        is_answered: true,
                        answer_state: "ANSWERED",
                        evaluation_status: "CORRECT",
                        marks_awarded: "10.00",
                        explanation: "Descriptive Explanation",
                        candidate_answer: { text_response: "My student descriptive answer." },
                        correct_answer: { model_answer: "The instructor model answer." },
                    },
                ],
                result: {
                    id: "res-all",
                    attempt_id: "att-all",
                    status: "FINAL",
                    score: "19.00",
                    maximum_score: "22.00",
                    percentage: "86.36",
                    total_questions: 6,
                    attempted_questions: 5,
                    correct_questions: 4,
                    incorrect_questions: 1,
                    partially_correct_questions: 0,
                    unanswered_questions: 1,
                    pending_evaluation_questions: 0,
                    finalized_at: "2026-10-04T00:45:00Z",
                    section_results: [],
                },
            });

            render(
                <MemoryRouter initialEntries={["/student/attempts/att-all/result"]}>
                    <Routes>
                        <Route
                            path="/student/attempts/:attemptId/result"
                            element={<StudentAttemptResultPage />}
                        />
                    </Routes>
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            await waitFor(() => {
                expect(screen.getByText("MCQ Question Text")).toBeInTheDocument();
                expect(screen.getByText("Multiple Select Question Text")).toBeInTheDocument();
                expect(screen.getByText("True False Question Text")).toBeInTheDocument();
                expect(screen.getByText("Assertion statement text")).toBeInTheDocument();
                expect(screen.getByText(/Left Item 1/i)).toBeInTheDocument();
                expect(screen.getByText("My student descriptive answer.")).toBeInTheDocument();
                expect(screen.getByText("The instructor model answer.")).toBeInTheDocument();
            });

            // Test filter button: click Incorrect (1)
            const incorrectBtn = screen.getByRole("button", { name: /Incorrect \(1\)/i });
            fireEvent.click(incorrectBtn);

            await waitFor(() => {
                expect(screen.getByText("Multiple Select Question Text")).toBeInTheDocument();
                expect(screen.queryByText("MCQ Question Text")).not.toBeInTheDocument();
            });
        });
    });

    describe("StudentAssessmentsPage integration", () => {
        it("triggers paper generation and starts attempt on click", async () => {
            vi.mocked(assessmentApi.listAssessments).mockResolvedValueOnce([
                {
                    id: "asm-1",
                    title: "Polity Mock 01",
                    description: "High yield questions",
                    type: "MOCK" as const,
                    status: "PUBLISHED" as const,
                    duration_seconds: 7200,
                    marks_per_question: "2.00",
                    penalty_per_question: "0.66",
                    created_at: "",
                    updated_at: "",
                },
            ]);

            vi.mocked(assessmentApi.generatePaper).mockResolvedValueOnce({
                id: "paper-1",
                assessment_id: "asm-1",
                status: "GENERATED",
                duration_seconds: 7200,
                marks_per_question: "2.00",
                penalty_per_question: "0.66",
                created_at: "",
                items: [],
            });

            vi.mocked(attemptsApi.startAttempt).mockResolvedValueOnce({
                id: "att-123",
                student_id: "stu-1",
                assessment_paper_id: "paper-1",
                attempt_number: 1,
                duration_seconds: 7200,
                started_at: "",
                expires_at: "",
                submitted_at: null,
                status: "IN_PROGRESS",
                items: [],
            });

            render(
                <MemoryRouter initialEntries={["/student/assessments"]}>
                    <Routes>
                        <Route
                            path="/student/assessments"
                            element={<StudentAssessmentsPage />}
                        />
                        <Route
                            path="/student/attempts/:attemptId"
                            element={<div>Attempt Workspace Loaded</div>}
                        />
                    </Routes>
                </MemoryRouter>,
                { wrapper: createWrapper() },
            );

            await waitFor(() => {
                expect(screen.getByText("Polity Mock 01")).toBeInTheDocument();
            });

            const startBtn = screen.getByRole("button", { name: "Start Assessment" });
            fireEvent.click(startBtn);

            await waitFor(() => {
                expect(assessmentApi.generatePaper).toHaveBeenCalledWith("asm-1");
                expect(attemptsApi.startAttempt).toHaveBeenCalledWith({
                    assessment_paper_id: "paper-1",
                });
                expect(screen.getByText("Attempt Workspace Loaded")).toBeInTheDocument();
            });
        });
    });
});
