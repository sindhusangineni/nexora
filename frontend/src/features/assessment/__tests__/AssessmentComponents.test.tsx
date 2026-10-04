import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

import {
    AssessmentStatusBadge,
    AssessmentTypeBadge,
} from "../components/AssessmentStatusBadge";
import { TaxonomySelector } from "../components/TaxonomySelector";
import { SectionManager } from "../components/SectionManager";
import { SelectionRuleList } from "../components/SelectionRuleList";
import { MarkingTimingConfiguration } from "../components/MarkingTimingConfiguration";
import { AssessmentLifecycleActions } from "../components/AssessmentLifecycleActions";
import { AssessmentReview } from "../components/AssessmentReview";
import { assessmentApi } from "../api/assessmentApi";
import { learningApi } from "@/features/learning";
import type {
    Assessment,
    AssessmentSection,
    SelectionRule,
} from "../types/assessment.types";

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>{children}</BrowserRouter>
        </QueryClientProvider>
    );
}

describe("Assessment Components", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe("AssessmentStatusBadge & AssessmentTypeBadge", () => {
        it("renders correct label for all assessment statuses", () => {
            const { rerender } = render(<AssessmentStatusBadge status="DRAFT" />);
            expect(screen.getByText("Draft")).toBeInTheDocument();

            rerender(<AssessmentStatusBadge status="PUBLISHED" />);
            expect(screen.getByText("Published")).toBeInTheDocument();

            rerender(<AssessmentStatusBadge status="ARCHIVED" />);
            expect(screen.getByText("Archived")).toBeInTheDocument();
        });

        it("renders correct label for assessment types", () => {
            const { rerender } = render(<AssessmentTypeBadge type="PRACTICE" />);
            expect(screen.getByText("Practice")).toBeInTheDocument();

            rerender(<AssessmentTypeBadge type="MOCK" />);
            expect(screen.getByText("Mock")).toBeInTheDocument();

            rerender(<AssessmentTypeBadge type="REVISION" />);
            expect(screen.getByText("Revision")).toBeInTheDocument();

            rerender(<AssessmentTypeBadge type="CUSTOM" />);
            expect(screen.getByText("Custom")).toBeInTheDocument();
        });
    });

    describe("TaxonomySelector", () => {
        it("renders scope select and loads domains", async () => {
            vi.spyOn(learningApi, "getDomains").mockResolvedValueOnce({
                count: 1,
                next: null,
                previous: null,
                results: [{ id: "dom-1", name: "General Studies", description: "", created_at: "", updated_at: "" }],
            });

            const handleChange = vi.fn();

            render(
                <TaxonomySelector
                    scopeType="DOMAIN"
                    scopeId=""
                    onChange={handleChange}
                />,
                { wrapper: createWrapper() },
            );

            expect(screen.getByLabelText(/taxonomy scope level/i)).toBeInTheDocument();

            await waitFor(() => {
                expect(screen.getByRole("option", { name: "General Studies" })).toBeInTheDocument();
            });

            fireEvent.change(screen.getByLabelText(/domain/i), {
                target: { value: "dom-1" },
            });

            expect(handleChange).toHaveBeenCalledWith("DOMAIN", "dom-1", "Domain: General Studies");
        });
    });

    describe("SectionManager", () => {
        const dummySections: AssessmentSection[] = [
            {
                id: "sec-1",
                assessment_id: "asm-1",
                title: "Section 1: Polity",
                description: "Indian Constitution and Polity",
                position: 0,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ];

        it("renders existing sections and handles add section modal", async () => {
            const user = userEvent.setup();
            render(
                <SectionManager
                    assessmentId="asm-1"
                    sections={dummySections}
                    isDraft={true}
                />,
                { wrapper: createWrapper() },
            );

            expect(screen.getByText("Section 1: Polity")).toBeInTheDocument();
            expect(screen.getByText("Indian Constitution and Polity")).toBeInTheDocument();

            const addBtn = screen.getByRole("button", { name: /add section/i });
            await user.click(addBtn);

            expect(screen.getByRole("dialog")).toBeInTheDocument();
            expect(screen.getByLabelText(/section title/i)).toBeInTheDocument();
        });

        it("allows deleting section in draft status", async () => {
            const user = userEvent.setup();
            const deleteSpy = vi.spyOn(assessmentApi, "deleteSection").mockResolvedValueOnce();

            render(
                <SectionManager
                    assessmentId="asm-1"
                    sections={dummySections}
                    isDraft={true}
                />,
                { wrapper: createWrapper() },
            );

            const deleteBtn = screen.getByRole("button", {
                name: /delete section section 1: polity/i,
            });
            await user.click(deleteBtn);

            expect(screen.getByText(/are you sure you want to delete this section/i)).toBeInTheDocument();

            const confirmBtn = screen.getByRole("button", { name: /confirm delete/i });
            await user.click(confirmBtn);

            expect(deleteSpy).toHaveBeenCalledWith("sec-1");
        });
    });

    describe("SelectionRuleList", () => {
        const dummyRules: SelectionRule[] = [
            {
                id: "rule-1",
                assessment_id: "asm-1",
                assessment_section_id: null,
                scope_type: "TOPIC",
                scope_id: "t-1",
                question_type: "MCQ",
                difficulty: "MEDIUM",
                question_count: 10,
                position: 0,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ];

        it("renders rules and displays deduplication warning", () => {
            render(
                <SelectionRuleList
                    assessmentId="asm-1"
                    rules={dummyRules}
                    sections={[]}
                    isDraft={true}
                />,
                { wrapper: createWrapper() },
            );

            expect(screen.getByText(/1 rule/i)).toBeInTheDocument();
            expect(screen.getByText(/~10 total questions/i)).toBeInTheDocument();
            expect(
                screen.getByText(/overlapping rules may resolve to fewer questions/i),
            ).toBeInTheDocument();
        });
    });

    describe("MarkingTimingConfiguration", () => {
        it("handles inputs and updates values properly", async () => {
            const user = userEvent.setup();
            const onDurationChange = vi.fn();
            const onMarksChange = vi.fn();
            const onPenaltyChange = vi.fn();
            const onPolicyChange = vi.fn();

            render(
                <MarkingTimingConfiguration
                    durationMinutes={120}
                    onDurationMinutesChange={onDurationChange}
                    marksPerQuestion="2.00"
                    onMarksPerQuestionChange={onMarksChange}
                    penaltyPerQuestion="0.66"
                    onPenaltyPerQuestionChange={onPenaltyChange}
                    scoreFloorPolicy="UNRESTRICTED"
                    onScoreFloorPolicyChange={onPolicyChange}
                />,
            );

            const durationInput = screen.getByLabelText(/assessment duration/i);
            await user.clear(durationInput);
            await user.type(durationInput, "90");

            expect(onDurationChange).toHaveBeenCalled();

            const policySelect = screen.getByLabelText(/scoring floor policy/i);
            await user.selectOptions(policySelect, "ZERO_FLOOR_TOTAL");

            expect(onPolicyChange).toHaveBeenCalledWith("ZERO_FLOOR_TOTAL");
        });
    });

    describe("AssessmentLifecycleActions", () => {
        const draftAssessment: Assessment = {
            id: "asm-draft",
            title: "Test Draft",
            description: "",
            type: "PRACTICE",
            status: "DRAFT",
            duration_seconds: 3600,
            marks_per_question: "2.00",
            penalty_per_question: "0.66",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        };

        const rule: SelectionRule = {
            id: "r-1",
            assessment_id: "asm-draft",
            assessment_section_id: null,
            scope_type: "TOPIC",
            scope_id: "t-1",
            question_type: null,
            difficulty: null,
            question_count: 5,
            position: 0,
            created_at: "",
            updated_at: "",
        };

        it("displays Publish button in DRAFT status and opens confirmation modal", async () => {
            const user = userEvent.setup();
            render(
                <AssessmentLifecycleActions
                    assessment={draftAssessment}
                    rules={[rule]}
                />,
                { wrapper: createWrapper() },
            );

            const publishBtn = screen.getByRole("button", { name: /publish assessment/i });
            expect(publishBtn).toBeEnabled();

            await user.click(publishBtn);

            expect(screen.getByText(/confirm publication/i)).toBeInTheDocument();
        });

        it("displays Generate Paper and Archive in PUBLISHED status", () => {
            const publishedAssessment: Assessment = {
                ...draftAssessment,
                status: "PUBLISHED",
            };

            render(
                <AssessmentLifecycleActions
                    assessment={publishedAssessment}
                    rules={[rule]}
                />,
                { wrapper: createWrapper() },
            );

            expect(screen.getByRole("button", { name: /generate assessment paper/i })).toBeInTheDocument();
            expect(screen.getByRole("button", { name: /archive assessment/i })).toBeInTheDocument();
            expect(screen.getByText(/published assessment:/i)).toBeInTheDocument();
        });
    });

    describe("AssessmentReview", () => {
        const assessment: Assessment = {
            id: "asm-review",
            title: "Review Assessment Mock",
            description: "Review test description",
            type: "MOCK",
            status: "DRAFT",
            duration_seconds: 7200,
            marks_per_question: "2.00",
            penalty_per_question: "0.66",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        };

        it("renders summary statistics and publication readiness checklist", () => {
            render(
                <AssessmentReview
                    assessment={assessment}
                    sections={[]}
                    rules={[]}
                    scoreFloorPolicy="ZERO_FLOOR_TOTAL"
                />,
            );

            expect(
                screen.getByRole("heading", { name: "Review Assessment Mock" }),
            ).toBeInTheDocument();
            expect(screen.getByText(/120 mins/i)).toBeInTheDocument();
            expect(
                screen.getAllByText(/\+2\.00 \/ -0\.66/i).length,
            ).toBeGreaterThan(0);
            expect(screen.getByText(/publication readiness checklist/i)).toBeInTheDocument();
            expect(screen.getByText(/incomplete requirements/i)).toBeInTheDocument();
        });
    });
});
