import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api";
import { assessmentApi } from "../api/assessmentApi";
import type {
    AssessmentCreatePayload,
    AssessmentUpdatePayload,
    RuleCreatePayload,
    SectionCreatePayload,
} from "../types/assessment.types";

describe("assessmentApi", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe("Assessments Lifecycle & CRUD", () => {
        it("calls GET /assessment/assessments/ to list assessments", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: [{ id: "asm-1", title: "Polity Mock 01", status: "DRAFT" }],
            });

            const result = await assessmentApi.listAssessments();

            expect(getSpy).toHaveBeenCalledWith("/assessment/assessments/");
            expect(result).toHaveLength(1);
            expect(result[0].title).toBe("Polity Mock 01");
        });

        it("calls GET /assessment/assessments/:id/ to retrieve assessment details", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { id: "asm-1", title: "Polity Mock 01", status: "DRAFT" },
            });

            const result = await assessmentApi.getAssessment("asm-1");

            expect(getSpy).toHaveBeenCalledWith("/assessment/assessments/asm-1/");
            expect(result.id).toBe("asm-1");
        });

        it("calls POST /assessment/assessments/ to create an assessment definition", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "asm-new", title: "New Mock", status: "DRAFT" },
            });

            const payload: AssessmentCreatePayload = {
                title: "New Mock",
                description: "Test description",
                type: "MOCK",
                duration_seconds: 7200,
                marks_per_question: "2.00",
                penalty_per_question: "0.66",
            };

            const result = await assessmentApi.createAssessment(payload);

            expect(postSpy).toHaveBeenCalledWith("/assessment/assessments/", payload);
            expect(result.id).toBe("asm-new");
        });

        it("calls PATCH /assessment/assessments/:id/ to update draft assessment", async () => {
            const patchSpy = vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
                data: { id: "asm-1", title: "Updated Mock", status: "DRAFT" },
            });

            const payload: AssessmentUpdatePayload = {
                title: "Updated Mock",
                duration_seconds: 5400,
            };

            const result = await assessmentApi.updateAssessment("asm-1", payload);

            expect(patchSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/",
                payload,
            );
            expect(result.title).toBe("Updated Mock");
        });

        it("calls POST /assessment/assessments/:id/publish/ to publish assessment", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "asm-1", status: "PUBLISHED" },
            });

            const result = await assessmentApi.publishAssessment("asm-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/publish/",
            );
            expect(result.status).toBe("PUBLISHED");
        });

        it("calls POST /assessment/assessments/:id/archive/ to archive assessment", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "asm-1", status: "ARCHIVED" },
            });

            const result = await assessmentApi.archiveAssessment("asm-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/archive/",
            );
            expect(result.status).toBe("ARCHIVED");
        });
    });

    describe("Assessment Sections", () => {
        it("calls GET /assessment/assessments/:id/sections/ to list sections", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: [
                    { id: "sec-1", title: "General Studies", position: 0 },
                    { id: "sec-2", title: "Current Affairs", position: 1 },
                ],
            });

            const result = await assessmentApi.listSections("asm-1");

            expect(getSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/sections/",
            );
            expect(result).toHaveLength(2);
            expect(result[0].title).toBe("General Studies");
        });

        it("calls POST /assessment/assessments/:id/sections/ to create a section", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "sec-new", title: "CSAT", position: 2 },
            });

            const payload: SectionCreatePayload = {
                title: "CSAT",
                description: "Aptitude and Reasoning",
                position: 2,
            };

            const result = await assessmentApi.createSection("asm-1", payload);

            expect(postSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/sections/",
                payload,
            );
            expect(result.id).toBe("sec-new");
        });

        it("calls DELETE /assessment/sections/:id/ to delete a section", async () => {
            const deleteSpy = vi.spyOn(apiClient, "delete").mockResolvedValueOnce({});

            await assessmentApi.deleteSection("sec-1");

            expect(deleteSpy).toHaveBeenCalledWith("/assessment/sections/sec-1/");
        });
    });

    describe("Selection Rules", () => {
        it("calls GET /assessment/assessments/:id/rules/ to list rules", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: [
                    {
                        id: "rule-1",
                        scope_type: "TOPIC",
                        scope_id: "topic-1",
                        question_count: 10,
                        position: 0,
                    },
                ],
            });

            const result = await assessmentApi.listRules("asm-1");

            expect(getSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/rules/",
            );
            expect(result).toHaveLength(1);
            expect(result[0].question_count).toBe(10);
        });

        it("calls POST /assessment/assessments/:id/rules/ to create a selection rule", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: {
                    id: "rule-new",
                    scope_type: "TOPIC",
                    scope_id: "topic-99",
                    question_type: "MCQ",
                    difficulty: "MEDIUM",
                    question_count: 5,
                    position: 1,
                },
            });

            const payload: RuleCreatePayload = {
                assessment_section_id: "sec-1",
                scope_type: "TOPIC",
                scope_id: "topic-99",
                question_type: "MCQ",
                difficulty: "MEDIUM",
                question_count: 5,
                position: 1,
            };

            const result = await assessmentApi.createRule("asm-1", payload);

            expect(postSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/rules/",
                payload,
            );
            expect(result.id).toBe("rule-new");
        });

        it("calls DELETE /assessment/rules/:id/ to delete a selection rule", async () => {
            const deleteSpy = vi.spyOn(apiClient, "delete").mockResolvedValueOnce({});

            await assessmentApi.deleteRule("rule-1");

            expect(deleteSpy).toHaveBeenCalledWith("/assessment/rules/rule-1/");
        });
    });

    describe("Paper Generation & Detail", () => {
        it("calls POST /assessment/assessments/:id/generate-paper/ to generate paper", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: {
                    id: "paper-123",
                    assessment_id: "asm-1",
                    status: "GENERATED",
                    items: [],
                },
            });

            const result = await assessmentApi.generatePaper("asm-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/assessment/assessments/asm-1/generate-paper/",
            );
            expect(result.id).toBe("paper-123");
            expect(result.status).toBe("GENERATED");
        });

        it("calls GET /assessment/papers/:id/ to fetch generated paper snapshot", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: {
                    id: "paper-123",
                    assessment_id: "asm-1",
                    items: [
                        {
                            id: "item-1",
                            question_id: "q-1",
                            question_version_id: "qv-1",
                            presentation_order: 1,
                        },
                    ],
                },
            });

            const result = await assessmentApi.getPaper("paper-123");

            expect(getSpy).toHaveBeenCalledWith("/assessment/papers/paper-123/");
            expect(result.id).toBe("paper-123");
            expect(result.items).toHaveLength(1);
        });
    });
});
