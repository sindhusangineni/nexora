import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AttemptWorkspace } from "../components/AttemptWorkspace";
import type { AttemptDelivery } from "../types/attempt.types";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { attemptsApi } from "../api/attemptsApi";

vi.mock("../api/attemptsApi", () => ({
    attemptsApi: {
        getStudentQuestionVersion: vi.fn(),
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

describe("AttemptWorkspace", () => {
    const mockAttempt: AttemptDelivery = {
        id: "att-1",
        student_id: "stu-1",
        assessment_paper_id: "paper-1",
        attempt_number: 1,
        duration_seconds: 3600,
        started_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        submitted_at: null,
        status: "IN_PROGRESS",
        items: [
            {
                id: "item-1",
                paper_item_id: "pitem-1",
                assessment_section_id: null,
                presentation_order: 1,
                allocated_marks: "2.0000",
                allocated_penalty: "0.5000",
                choices: [
                    { id: "c1", choice_id: "c1", presented_position: 1 },
                    { id: "c2", choice_id: "c2", presented_position: 2 },
                ],
                response: {
                    id: "resp-1",
                    answer_state: "UNANSWERED",
                    boolean_response: null,
                    assertion_reason_response: null,
                    text_response: null,
                    selected_choice_ids: [],
                    selected_matches: [],
                },
            },
            {
                id: "item-2",
                paper_item_id: "pitem-2",
                assessment_section_id: null,
                presentation_order: 2,
                allocated_marks: "2.0000",
                allocated_penalty: "0.0000",
                choices: [],
                response: {
                    id: "resp-2",
                    answer_state: "ANSWERED",
                    boolean_response: true,
                    assertion_reason_response: null,
                    text_response: null,
                    selected_choice_ids: [],
                    selected_matches: [],
                },
            },
        ],
    };

    const mockAssessment = {
        id: "asm-1",
        title: "Mock UPSC Polity",
        description: "Standard mock test",
        type: "MOCK" as const,
        status: "PUBLISHED" as const,
        duration_seconds: 3600,
        marks_per_question: "2.00",
        penalty_per_question: "0.50",
        created_at: "",
        updated_at: "",
    };

    const mockPaper = {
        id: "paper-1",
        assessment_id: "asm-1",
        status: "GENERATED" as const,
        duration_seconds: 3600,
        marks_per_question: "2.00",
        penalty_per_question: "0.50",
        created_at: "",
        items: [
            {
                id: "pitem-1",
                paper_id: "paper-1",
                question_id: "q-1",
                question_version_id: "ver-1",
                assessment_section_id: null,
                presentation_order: 1,
                allocated_marks: "2.00",
                allocated_penalty: "0.50",
                created_at: "",
            },
            {
                id: "pitem-2",
                paper_id: "paper-1",
                question_id: "q-2",
                question_version_id: "ver-2",
                assessment_section_id: null,
                presentation_order: 2,
                allocated_marks: "2.00",
                allocated_penalty: "0.00",
                created_at: "",
            },
        ],
    };

    it("renders workspace, header, timer, progress, and first question", async () => {
        vi.mocked(attemptsApi.getStudentQuestionVersion).mockResolvedValueOnce({
            id: "ver-1",
            question_id: "q-1",
            version_number: 1,
            question_type: "MCQ",
            difficulty: "MEDIUM",
            text: "Which Article guarantees equality before law?",
            content: {
                choices: [
                    { id: "c1", text: "Article 14", position: 1 },
                    { id: "c2", text: "Article 19", position: 2 },
                ],
            },
        });

        const handleSave = vi.fn().mockResolvedValue(undefined);
        const handleClear = vi.fn().mockResolvedValue(undefined);
        const handleSubmit = vi.fn().mockResolvedValue(undefined);

        render(
            <AttemptWorkspace
                attempt={mockAttempt}
                assessment={mockAssessment}
                paper={mockPaper}
                onSaveResponse={handleSave}
                onClearResponse={handleClear}
                onSubmitAttempt={handleSubmit}
            />,
            { wrapper: createWrapper() },
        );

        expect(screen.getByText("Mock UPSC Polity")).toBeInTheDocument();
        expect(screen.getByText("Attempt #1")).toBeInTheDocument();
        expect(screen.getByRole("timer")).toBeInTheDocument();
        expect(screen.getByText(/1 of 2 Answered/i)).toBeInTheDocument();

        await waitFor(() => {
            expect(
                screen.getByText("Which Article guarantees equality before law?"),
            ).toBeInTheDocument();
            expect(screen.getByText("Article 14")).toBeInTheDocument();
        });
    });

    it("navigates between questions using Next and Previous", async () => {
        vi.mocked(attemptsApi.getStudentQuestionVersion)
            .mockResolvedValueOnce({
                id: "ver-1",
                question_id: "q-1",
                version_number: 1,
                question_type: "MCQ",
                difficulty: "MEDIUM",
                text: "Question 1 text",
                content: { choices: [] },
            })
            .mockResolvedValueOnce({
                id: "ver-2",
                question_id: "q-2",
                version_number: 1,
                question_type: "TRUE_FALSE",
                difficulty: "EASY",
                text: "Question 2 text",
                content: {},
            });

        render(
            <AttemptWorkspace
                attempt={mockAttempt}
                assessment={mockAssessment}
                paper={mockPaper}
                onSaveResponse={vi.fn()}
                onClearResponse={vi.fn()}
                onSubmitAttempt={vi.fn()}
            />,
            { wrapper: createWrapper() },
        );

        await waitFor(() => {
            expect(screen.getByText("Question 1 of 2")).toBeInTheDocument();
        });

        const nextBtn = screen.getByRole("button", { name: "Next" });
        fireEvent.click(nextBtn);

        await waitFor(() => {
            expect(screen.getByText("Question 2 of 2")).toBeInTheDocument();
        });

        const prevBtn = screen.getByRole("button", { name: "Previous" });
        fireEvent.click(prevBtn);

        await waitFor(() => {
            expect(screen.getByText("Question 1 of 2")).toBeInTheDocument();
        });
    });

    it("opens submission confirmation modal and triggers submit", async () => {
        const handleSubmit = vi.fn().mockResolvedValue(undefined);

        render(
            <AttemptWorkspace
                attempt={mockAttempt}
                assessment={mockAssessment}
                onSaveResponse={vi.fn()}
                onClearResponse={vi.fn()}
                onSubmitAttempt={handleSubmit}
            />,
            { wrapper: createWrapper() },
        );

        const submitBtn = screen.getByRole("button", { name: "Submit Test" });
        fireEvent.click(submitBtn);

        expect(screen.getByText("Submit Assessment")).toBeInTheDocument();
        expect(screen.getByText(/You have 1 unanswered question/i)).toBeInTheDocument();

        const confirmBtn = screen.getByRole("button", { name: "Confirm & Submit" });
        fireEvent.click(confirmBtn);

        await waitFor(() => {
            expect(handleSubmit).toHaveBeenCalled();
        });
    });

    it("displays read-only warning when attempt is SUBMITTED or EVALUATED", () => {
        const submittedAttempt: AttemptDelivery = {
            ...mockAttempt,
            status: "SUBMITTED",
        };

        render(
            <AttemptWorkspace
                attempt={submittedAttempt}
                assessment={mockAssessment}
                onSaveResponse={vi.fn()}
                onClearResponse={vi.fn()}
                onSubmitAttempt={vi.fn()}
            />,
            { wrapper: createWrapper() },
        );

        expect(screen.getByText(/Read-Only Session:/i)).toBeInTheDocument();
    });
});
