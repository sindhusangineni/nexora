import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { LifecycleActions } from "../components/LifecycleActions";
import { questionBankApi } from "../api/questionBankApi";

function renderWithClient(ui: React.ReactElement) {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });
    return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("LifecycleActions Component", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("renders 'Submit for Review' for DRAFT versions and performs mutation upon confirmation", async () => {
        const user = userEvent.setup();
        const submitSpy = vi
            .spyOn(questionBankApi, "submitReview")
            .mockResolvedValueOnce({
                id: "v-1",
                question_id: "q-1",
                version_number: 1,
                status: "REVIEW",
                question_type: "MCQ",
                text: "Test question",
                difficulty: "MEDIUM",
                explanation: "",
                content: { choices: [] },
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
            });

        renderWithClient(
            <LifecycleActions
                questionId="q-1"
                versionId="v-1"
                versionNumber={1}
                status="DRAFT"
            />,
        );

        const actionBtn = screen.getByRole("button", { name: /submit for review/i });
        expect(actionBtn).toBeInTheDocument();

        // Click action button to open confirmation modal
        await user.click(actionBtn);

        // Confirmation modal appears
        expect(
            screen.getByRole("heading", { name: /submit version v1 for review/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/this will change the status to 'under review'/i),
        ).toBeInTheDocument();

        // Confirm
        const submitButtons = screen.getAllByRole("button", {
            name: /submit for review/i,
        });
        await user.click(submitButtons[submitButtons.length - 1]);

        expect(submitSpy).toHaveBeenCalledWith("q-1", "v-1");
    });

    it("renders 'Approve' for REVIEW versions", async () => {
        renderWithClient(
            <LifecycleActions
                questionId="q-1"
                versionId="v-1"
                versionNumber={1}
                status="REVIEW"
            />,
        );

        expect(screen.getByRole("button", { name: /approve/i })).toBeInTheDocument();
    });

    it("renders 'Publish' for APPROVED versions", async () => {
        renderWithClient(
            <LifecycleActions
                questionId="q-1"
                versionId="v-1"
                versionNumber={1}
                status="APPROVED"
            />,
        );

        expect(screen.getByRole("button", { name: /publish/i })).toBeInTheDocument();
    });

    it("renders 'Archive' and '+ Create New Version' for PUBLISHED versions", async () => {
        const onCreateNewVersion = vi.fn();

        renderWithClient(
            <LifecycleActions
                questionId="q-1"
                versionId="v-1"
                versionNumber={1}
                status="PUBLISHED"
                onCreateNewVersion={onCreateNewVersion}
            />,
        );

        expect(screen.getByRole("button", { name: /archive/i })).toBeInTheDocument();
        const newVerBtn = screen.getByRole("button", {
            name: /\+ create new version/i,
        });
        expect(newVerBtn).toBeInTheDocument();

        const user = userEvent.setup();
        await user.click(newVerBtn);
        expect(onCreateNewVersion).toHaveBeenCalled();
    });
});
