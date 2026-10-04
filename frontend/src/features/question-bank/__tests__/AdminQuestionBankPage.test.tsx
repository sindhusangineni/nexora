import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AdminQuestionBankPage } from "@/pages/admin/AdminQuestionBankPage";
import { questionBankApi } from "../api/questionBankApi";
import type { QuestionListResponse } from "../types/questionBank.types";

const mockQuestionsResponse: QuestionListResponse = {
    count: 2,
    next: null,
    previous: null,
    results: [
        {
            id: "q-1",
            topic_ids: ["t-1"],
            version_count: 3,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-02T00:00:00Z",
            published_version: {
                id: "v-pub-1",
                question_id: "q-1",
                version_number: 2,
                status: "PUBLISHED",
                question_type: "MCQ",
                text: "Which Schedule contains the list of recognized languages?",
                difficulty: "MEDIUM",
                explanation: "",
                content: { choices: [] },
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
            },
            latest_version: {
                id: "v-lat-1",
                question_id: "q-1",
                version_number: 3,
                status: "DRAFT",
                question_type: "MCQ",
                text: "Which Schedule contains the list of recognized languages? (Revised)",
                difficulty: "MEDIUM",
                explanation: "",
                content: { choices: [] },
                created_at: "2026-01-02T00:00:00Z",
                updated_at: "2026-01-02T00:00:00Z",
            },
        },
        {
            id: "q-2",
            topic_ids: [],
            version_count: 1,
            created_at: "2026-01-03T00:00:00Z",
            updated_at: "2026-01-03T00:00:00Z",
            published_version: null,
            latest_version: {
                id: "v-lat-2",
                question_id: "q-2",
                version_number: 1,
                status: "REVIEW",
                question_type: "DESCRIPTIVE",
                text: "Discuss the key features of the 73rd Constitutional Amendment Act.",
                difficulty: "HARD",
                explanation: "",
                content: {},
                created_at: "2026-01-03T00:00:00Z",
                updated_at: "2026-01-03T00:00:00Z",
            },
        },
    ],
};

function renderWithProviders(ui: React.ReactElement) {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });

    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>{ui}</MemoryRouter>
        </QueryClientProvider>,
    );
}

describe("AdminQuestionBankPage", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("renders questions list, status tabs, and create action", async () => {
        vi.spyOn(questionBankApi, "listQuestions").mockResolvedValueOnce(
            mockQuestionsResponse,
        );

        renderWithProviders(<AdminQuestionBankPage />);

        expect(screen.getByRole("heading", { name: /question bank/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /\+ create question/i })).toBeInTheDocument();

        // Check tabs
        expect(screen.getByRole("button", { name: /all questions/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /^draft$/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /^published$/i })).toBeInTheDocument();

        // Wait for questions to load
        await waitFor(() => {
            expect(
                screen.getByText(/Which Schedule contains the list of recognized languages\?/i),
            ).toBeInTheDocument();
        });

        expect(
            screen.getByText(/Discuss the key features of the 73rd Constitutional Amendment Act\./i),
        ).toBeInTheDocument();

        // Check status badges
        expect(screen.getAllByText("Draft").length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("In Review").length).toBeGreaterThanOrEqual(1);
    });

    it("renders empty state when no questions match the filters", async () => {
        vi.spyOn(questionBankApi, "listQuestions").mockResolvedValueOnce({
            count: 0,
            next: null,
            previous: null,
            results: [],
        });

        renderWithProviders(<AdminQuestionBankPage />);

        await waitFor(() => {
            expect(screen.getByText(/no questions found/i)).toBeInTheDocument();
        });
    });

    it("triggers filter updates when switching tabs", async () => {
        const user = userEvent.setup();
        const listSpy = vi
            .spyOn(questionBankApi, "listQuestions")
            .mockResolvedValue(mockQuestionsResponse);

        renderWithProviders(<AdminQuestionBankPage />);

        const publishedTab = screen.getByRole("button", { name: /^published$/i });
        await user.click(publishedTab);

        expect(listSpy).toHaveBeenCalledWith(
            expect.objectContaining({ status: "PUBLISHED" }),
        );
    });
});
