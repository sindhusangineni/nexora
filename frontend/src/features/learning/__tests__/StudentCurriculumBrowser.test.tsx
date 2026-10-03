import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { StudentCurriculumBrowser } from "../components/StudentCurriculumBrowser";
import { learningApi } from "../api/learningApi";
import { ApiError } from "@/lib/api";

const mockDomains = {
    count: 2,
    next: null,
    previous: null,
    results: [
        {
            id: "domain-1",
            name: "UPSC Civil Services",
            description: "General Studies curriculum",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        },
        {
            id: "domain-2",
            name: "State PSC",
            description: "State civil services curriculum",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        },
    ],
};

const mockSubjects = {
    count: 1,
    next: null,
    previous: null,
    results: [
        {
            id: "subject-1",
            domain: "domain-1",
            name: "Indian History",
            description: "Ancient, medieval and modern",
            position: 1,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        },
    ],
};

const mockChapters = {
    count: 1,
    next: null,
    previous: null,
    results: [
        {
            id: "chapter-1",
            subject: "subject-1",
            name: "Modern India",
            description: "Colonial rule to independence",
            position: 1,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        },
    ],
};

const mockTopics = {
    count: 1,
    next: null,
    previous: null,
    results: [
        {
            id: "topic-1",
            chapter: "chapter-1",
            name: "Quit India Movement 1942",
            description: "Do or Die resolution and underground movements",
            position: 1,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        },
    ],
};

function renderWithQueryClient(ui: React.ReactElement) {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false, gcTime: 0 },
        },
    });
    return render(
        <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
    );
}

describe("StudentCurriculumBrowser Component", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("renders domains list on initial load", async () => {
        vi.spyOn(learningApi, "getDomains").mockResolvedValueOnce(mockDomains);

        renderWithQueryClient(<StudentCurriculumBrowser />);

        expect(screen.getByText("Curriculum & Learning")).toBeInTheDocument();
        expect(
            screen.getByText("Loading curriculum domains..."),
        ).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });
        expect(screen.getByText("State PSC")).toBeInTheDocument();
    });

    it("does not render any admin mutation buttons to students", async () => {
        vi.spyOn(learningApi, "getDomains").mockResolvedValueOnce(mockDomains);

        renderWithQueryClient(<StudentCurriculumBrowser />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        expect(
            screen.queryByRole("button", { name: /\+ new domain/i }),
        ).not.toBeInTheDocument();
        expect(screen.queryByTitle("Edit Domain")).not.toBeInTheDocument();
        expect(screen.queryByTitle("Delete Domain")).not.toBeInTheDocument();
    });

    it("navigates down hierarchy: Domain -> Subject -> Chapter -> Topic", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        vi.spyOn(learningApi, "getSubjects").mockResolvedValue(mockSubjects);
        vi.spyOn(learningApi, "getChapters").mockResolvedValue(mockChapters);
        vi.spyOn(learningApi, "getTopics").mockResolvedValue(mockTopics);

        renderWithQueryClient(<StudentCurriculumBrowser />);

        // 1. Wait for domains and select UPSC
        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });
        await user.click(screen.getByText("UPSC Civil Services"));

        // 2. Wait for subjects
        await waitFor(() => {
            expect(screen.getByText("Indian History")).toBeInTheDocument();
        });
        expect(
            screen.getByText("Subjects in UPSC Civil Services"),
        ).toBeInTheDocument();

        // 3. Select Subject
        await user.click(screen.getByText("Indian History"));

        // 4. Wait for chapters
        await waitFor(() => {
            expect(screen.getByText("Modern India")).toBeInTheDocument();
        });
        expect(
            screen.getByText("Chapters in Indian History"),
        ).toBeInTheDocument();

        // 5. Select Chapter
        await user.click(screen.getByText("Modern India"));

        // 6. Wait for topics
        await waitFor(() => {
            expect(
                screen.getByText("Quit India Movement 1942"),
            ).toBeInTheDocument();
        });
        expect(
            screen.getByText(
                "Do or Die resolution and underground movements",
            ),
        ).toBeInTheDocument();
    });

    it("navigates back using breadcrumbs", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        vi.spyOn(learningApi, "getSubjects").mockResolvedValue(mockSubjects);

        renderWithQueryClient(<StudentCurriculumBrowser />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        // Click into Domain
        await user.click(screen.getByText("UPSC Civil Services"));
        await waitFor(() => {
            expect(screen.getByText("Indian History")).toBeInTheDocument();
        });

        // Click "Curriculum" breadcrumb to navigate back to root
        const curriculumBreadcrumb = screen.getByRole("button", {
            name: "Curriculum",
        });
        await user.click(curriculumBreadcrumb);

        await waitFor(() => {
            expect(screen.getByText("Available Domains")).toBeInTheDocument();
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });
    });

    it("displays error message and handles retry", async () => {
        const user = userEvent.setup();
        const getDomainsSpy = vi
            .spyOn(learningApi, "getDomains")
            .mockRejectedValueOnce(
                new ApiError({
                    code: "NETWORK_ERROR",
                    message: "Server unreachable",
                    isNetworkError: true,
                }),
            )
            .mockResolvedValueOnce(mockDomains);

        renderWithQueryClient(<StudentCurriculumBrowser />);

        await waitFor(() => {
            expect(screen.getByRole("alert")).toHaveTextContent(
                "Server unreachable",
            );
        });

        const retryBtn = screen.getByRole("button", { name: /retry/i });
        await user.click(retryBtn);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });
        expect(getDomainsSpy).toHaveBeenCalledTimes(2);
    });

    it("renders empty state when no domains exist", async () => {
        vi.spyOn(learningApi, "getDomains").mockResolvedValueOnce({
            count: 0,
            next: null,
            previous: null,
            results: [],
        });

        renderWithQueryClient(<StudentCurriculumBrowser />);

        await waitFor(() => {
            expect(
                screen.getByText("No curriculum domains are currently available."),
            ).toBeInTheDocument();
        });
    });
});
