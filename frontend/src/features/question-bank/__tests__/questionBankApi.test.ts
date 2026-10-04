import { describe, it, expect, vi, beforeEach } from "vitest";

import { apiClient } from "@/lib/api";
import { questionBankApi } from "../api/questionBankApi";
import type {
    QuestionFilterParams,
    QuestionCreatePayload,
    QuestionVersionCreatePayload,
    QuestionVersionPatchPayload,
} from "../types/questionBank.types";

describe("questionBankApi", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe("Question Root API", () => {
        it("calls GET /question-bank/questions/ with query parameters", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { count: 1, next: null, previous: null, results: [] },
            });

            const params: QuestionFilterParams = {
                status: "PUBLISHED",
                question_type: "MCQ",
                difficulty: "MEDIUM",
                search: "Parliament",
                page: 2,
            };

            await questionBankApi.listQuestions(params);

            expect(getSpy).toHaveBeenCalledWith("/question-bank/questions/", {
                params: {
                    status: "PUBLISHED",
                    question_type: "MCQ",
                    difficulty: "MEDIUM",
                    search: "Parliament",
                    page: 2,
                },
            });
        });

        it("calls GET /question-bank/questions/:id/ to fetch single question", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { id: "q-1", topic_ids: ["t-1"], versions_count: 1 },
            });

            const result = await questionBankApi.getQuestion("q-1");

            expect(getSpy).toHaveBeenCalledWith("/question-bank/questions/q-1/");
            expect(result.id).toBe("q-1");
        });

        it("calls POST /question-bank/questions/ to create question with initial draft", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "q-created", topic_ids: ["t-10"] },
            });

            const payload: QuestionCreatePayload = {
                question_type: "MCQ",
                text: "Which of the following is correct?",
                difficulty: "HARD",
                explanation: "Detailed explanation",
                topic_ids: ["t-10"],
                source_type: "UPSC_PREVIOUS_YEAR",
                source_name: "UPSC Prelims",
                source_year: 2024,
                choices: [
                    { text: "Option A", is_correct: true, position: 1 },
                    { text: "Option B", is_correct: false, position: 2 },
                ],
            };

            const result = await questionBankApi.createQuestion(payload);

            expect(postSpy).toHaveBeenCalledWith("/question-bank/questions/", payload);
            expect(result.id).toBe("q-created");
        });
    });

    describe("Question Versions API", () => {
        it("calls GET /question-bank/questions/:id/versions/ to list versions", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { count: 2, next: null, previous: null, results: [] },
            });

            await questionBankApi.listQuestionVersions("q-1");

            expect(getSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/",
                { params: undefined },
            );
        });

        it("calls GET /question-bank/questions/:id/versions/:vid/ to fetch admin version detail", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { id: "v-1", version_number: 1, status: "DRAFT" },
            });

            const result = await questionBankApi.getQuestionVersion("q-1", "v-1");

            expect(getSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/v-1/",
            );
            expect(result.version_number).toBe(1);
        });

        it("calls POST /question-bank/questions/:id/versions/ to create a new version", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "v-2", version_number: 2, status: "DRAFT" },
            });

            const payload: QuestionVersionCreatePayload = {
                question_type: "TRUE_FALSE",
                text: "The President can dissolve the Lok Sabha.",
                difficulty: "EASY",
                true_false: { answer: true },
            };

            const result = await questionBankApi.createQuestionVersion("q-1", payload);

            expect(postSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/",
                payload,
            );
            expect(result.version_number).toBe(2);
        });

        it("calls PATCH /question-bank/questions/:id/versions/:vid/ to update draft version", async () => {
            const patchSpy = vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
                data: { id: "v-1", text: "Updated text" },
            });

            const payload: QuestionVersionPatchPayload = {
                text: "Updated text",
                difficulty: "MEDIUM",
            };

            const result = await questionBankApi.updateDraftVersion("q-1", "v-1", payload);

            expect(patchSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/v-1/",
                payload,
            );
            expect(result.text).toBe("Updated text");
        });
    });

    describe("Lifecycle Transitions", () => {
        it("calls POST submit-review endpoint", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "v-1", status: "REVIEW" },
            });

            const result = await questionBankApi.submitReview("q-1", "v-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/v-1/submit-review/",
            );
            expect(result.status).toBe("REVIEW");
        });

        it("calls POST approve endpoint", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "v-1", status: "APPROVED" },
            });

            const result = await questionBankApi.approveVersion("q-1", "v-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/v-1/approve/",
            );
            expect(result.status).toBe("APPROVED");
        });

        it("calls POST publish endpoint", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "v-1", status: "PUBLISHED" },
            });

            const result = await questionBankApi.publishVersion("q-1", "v-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/v-1/publish/",
            );
            expect(result.status).toBe("PUBLISHED");
        });

        it("calls POST archive endpoint", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "v-1", status: "ARCHIVED" },
            });

            const result = await questionBankApi.archiveVersion("q-1", "v-1");

            expect(postSpy).toHaveBeenCalledWith(
                "/question-bank/questions/q-1/versions/v-1/archive/",
            );
            expect(result.status).toBe("ARCHIVED");
        });
    });
});
