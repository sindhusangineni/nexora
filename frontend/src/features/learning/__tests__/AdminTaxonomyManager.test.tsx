import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AdminTaxonomyManager } from "../components/AdminTaxonomyManager";
import { learningApi } from "../api/learningApi";
import { ApiError } from "@/lib/api";

const mockDomains = {
    count: 1,
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
            description: "History overview",
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
            mutations: { retry: false },
        },
    });
    return render(
        <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
    );
}

describe("AdminTaxonomyManager Component", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("renders domains and management controls", async () => {
        vi.spyOn(learningApi, "getDomains").mockResolvedValueOnce(mockDomains);

        renderWithQueryClient(<AdminTaxonomyManager />);

        expect(
            screen.getByText("Learning Taxonomy Management"),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /\+ new domain/i }),
        ).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });
    });

    it("successfully creates a new domain via modal form", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        const createSpy = vi.spyOn(learningApi, "createDomain").mockResolvedValueOnce({
            id: "domain-2",
            name: "State PSC",
            description: "State level exams",
            created_at: "2026-01-02T00:00:00Z",
            updated_at: "2026-01-02T00:00:00Z",
        });

        renderWithQueryClient(<AdminTaxonomyManager />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        // Open modal
        await user.click(screen.getByRole("button", { name: /\+ new domain/i }));

        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Create New Domain")).toBeInTheDocument();

        // Fill form
        await user.type(screen.getByLabelText(/domain name/i), "State PSC");
        await user.type(
            screen.getByLabelText(/description/i),
            "State level exams",
        );

        // Submit
        await user.click(screen.getByRole("button", { name: "Create Domain" }));

        await waitFor(() => {
            expect(createSpy).toHaveBeenCalledWith({
                name: "State PSC",
                description: "State level exams",
            });
        });
    });

    it("successfully updates an existing domain via modal form", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        const updateSpy = vi.spyOn(learningApi, "updateDomain").mockResolvedValueOnce({
            id: "domain-1",
            name: "UPSC Updated",
            description: "Updated description",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-02T00:00:00Z",
        });

        renderWithQueryClient(<AdminTaxonomyManager />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        // Click edit
        await user.click(
            screen.getByRole("button", { name: "Edit Domain UPSC Civil Services" }),
        );

        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Edit Domain")).toBeInTheDocument();

        const nameInput = screen.getByLabelText(/domain name/i);
        await user.clear(nameInput);
        await user.type(nameInput, "UPSC Updated");

        await user.click(screen.getByRole("button", { name: "Save Changes" }));

        await waitFor(() => {
            expect(updateSpy).toHaveBeenCalledWith("domain-1", {
                name: "UPSC Updated",
                description: "General Studies curriculum",
            });
        });
    });

    it("handles domain deletion confirmation", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        const deleteSpy = vi.spyOn(learningApi, "deleteDomain").mockResolvedValueOnce();

        renderWithQueryClient(<AdminTaxonomyManager />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        // Click delete
        await user.click(
            screen.getByRole("button", { name: "Delete Domain UPSC Civil Services" }),
        );

        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "Delete Domain" }),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Are you sure you want to delete this domain\?/i),
        ).toBeInTheDocument();

        // Confirm delete
        const confirmBtn = screen.getByRole("button", {
            name: "Delete Domain",
        });
        await user.click(confirmBtn);

        await waitFor(() => {
            expect(deleteSpy).toHaveBeenCalledWith("domain-1");
        });
    });

    it("displays error when deleting a resource with active children (409 Conflict)", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        vi.spyOn(learningApi, "deleteDomain").mockRejectedValueOnce(
            new ApiError({
                code: "PROTECTED_RESOURCE",
                message:
                    "Cannot delete domain because it is referenced by active child resources. Delete or reassign child resources first.",
                status: 409,
            }),
        );

        renderWithQueryClient(<AdminTaxonomyManager />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        await user.click(
            screen.getByRole("button", { name: "Delete Domain UPSC Civil Services" }),
        );

        const confirmBtn = screen.getByRole("button", {
            name: "Delete Domain",
        });
        await user.click(confirmBtn);

        await waitFor(() => {
            expect(screen.getByRole("alert")).toHaveTextContent(
                "Cannot delete domain because it is referenced by active child resources.",
            );
        });
    });

    it("selects domain and allows creating subject", async () => {
        const user = userEvent.setup();
        vi.spyOn(learningApi, "getDomains").mockResolvedValue(mockDomains);
        vi.spyOn(learningApi, "getSubjects").mockResolvedValue(mockSubjects);
        const createSubjectSpy = vi
            .spyOn(learningApi, "createSubject")
            .mockResolvedValueOnce({
                id: "subject-2",
                domain: "domain-1",
                name: "Geography",
                description: "World and Indian Geography",
                position: 2,
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
            });

        renderWithQueryClient(<AdminTaxonomyManager />);

        await waitFor(() => {
            expect(screen.getByText("UPSC Civil Services")).toBeInTheDocument();
        });

        // Click domain to load subjects
        await user.click(screen.getByText("UPSC Civil Services"));

        await waitFor(() => {
            expect(screen.getByText("Indian History")).toBeInTheDocument();
        });

        // Click "+ Add" on subjects column
        const addSubjectBtn = screen.getByRole("button", { name: /\+ add/i });
        await user.click(addSubjectBtn);

        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Create New Subject")).toBeInTheDocument();

        await user.type(screen.getByLabelText(/subject name/i), "Geography");
        await user.click(screen.getByRole("button", { name: "Create Subject" }));

        await waitFor(() => {
            expect(createSubjectSpy).toHaveBeenCalledWith({
                domain: "domain-1",
                name: "Geography",
                description: "",
                position: 0,
            });
        });
    });
});
