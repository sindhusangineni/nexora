import { describe, it, expect, vi, beforeEach } from "vitest";
import { attemptsApi } from "../api/attemptsApi";
import { apiClient } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
    apiClient: {
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
    },
}));

describe("attemptsApi", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("getAttemptHistory fetches from /attempts/ without params", async () => {
        const mockHistory = {
            count: 0,
            next: null,
            previous: null,
            results: [],
        };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockHistory });

        const res = await attemptsApi.getAttemptHistory();
        expect(apiClient.get).toHaveBeenCalledWith("/attempts/");
        expect(res).toEqual(mockHistory);
    });

    it("getAttemptHistory formats query parameters properly", async () => {
        const mockHistory = {
            count: 1,
            next: null,
            previous: null,
            results: [{ id: "att-1" }],
        };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockHistory });

        const res = await attemptsApi.getAttemptHistory({
            status: "IN_PROGRESS",
            page: 2,
            page_size: 10,
        });
        expect(apiClient.get).toHaveBeenCalledWith(
            "/attempts/?status=IN_PROGRESS&page=2&page_size=10",
        );
        expect(res).toEqual(mockHistory);
    });

    it("startAttempt posts to /attempts/ with payload", async () => {
        const mockAttempt = {
            id: "att-1",
            student_id: "stu-1",
            assessment_paper_id: "paper-1",
            attempt_number: 1,
            status: "IN_PROGRESS",
            items: [],
        };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockAttempt });

        const res = await attemptsApi.startAttempt({ assessment_paper_id: "paper-1" });
        expect(apiClient.post).toHaveBeenCalledWith("/attempts/", {
            assessment_paper_id: "paper-1",
        });
        expect(res).toEqual(mockAttempt);
    });

    it("getAttempt fetches from /attempts/:id/", async () => {
        const mockAttempt = {
            id: "att-1",
            status: "IN_PROGRESS",
            items: [],
        };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockAttempt });

        const res = await attemptsApi.getAttempt("att-1");
        expect(apiClient.get).toHaveBeenCalledWith("/attempts/att-1/");
        expect(res).toEqual(mockAttempt);
    });

    it("saveResponse puts to /attempts/:attemptId/items/:itemId/response/", async () => {
        const mockResp = {
            id: "resp-1",
            answer_state: "ANSWERED",
            selected_choice_ids: ["c-1"],
        };
        vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockResp });

        const res = await attemptsApi.saveResponse("att-1", "item-1", {
            choice_id: "c-1",
        });
        expect(apiClient.put).toHaveBeenCalledWith(
            "/attempts/att-1/items/item-1/response/",
            { choice_id: "c-1" },
        );
        expect(res).toEqual(mockResp);
    });

    it("clearResponse deletes to /attempts/:attemptId/items/:itemId/response/", async () => {
        const mockResp = {
            id: "resp-1",
            answer_state: "UNANSWERED",
            selected_choice_ids: [],
        };
        vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockResp });

        const res = await attemptsApi.clearResponse("att-1", "item-1");
        expect(apiClient.delete).toHaveBeenCalledWith(
            "/attempts/att-1/items/item-1/response/",
        );
        expect(res).toEqual(mockResp);
    });

    it("submitAttempt posts to /attempts/:id/submit/", async () => {
        const mockSubmitted = {
            id: "att-1",
            status: "EVALUATED",
        };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockSubmitted });

        const res = await attemptsApi.submitAttempt("att-1");
        expect(apiClient.post).toHaveBeenCalledWith("/attempts/att-1/submit/");
        expect(res).toEqual(mockSubmitted);
    });

    it("getAttemptResult fetches from /attempts/:id/result/", async () => {
        const mockResult = {
            id: "res-1",
            status: "FINAL",
            score: "2.00",
            maximum_score: "2.00",
        };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResult });

        const res = await attemptsApi.getAttemptResult("att-1");
        expect(apiClient.get).toHaveBeenCalledWith("/attempts/att-1/result/");
        expect(res).toEqual(mockResult);
    });

    it("getStudentQuestionVersion fetches sanitized question content", async () => {
        const mockVersion = {
            id: "ver-1",
            question_id: "q-1",
            version_number: 1,
            question_type: "MCQ",
            text: "Question text",
            content: { choices: [] },
        };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockVersion });

        const res = await attemptsApi.getStudentQuestionVersion("q-1", "ver-1");
        expect(apiClient.get).toHaveBeenCalledWith(
            "/question-bank/questions/q-1/versions/ver-1/",
        );
        expect(res).toEqual(mockVersion);
    });

    it("cancelAttempt posts to /attempts/:id/cancel/", async () => {
        const mockCancelled = {
            id: "att-1",
            status: "CANCELLED",
        };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockCancelled });

        const res = await attemptsApi.cancelAttempt("att-1", {
            reason: "Admin cancelled",
        });
        expect(apiClient.post).toHaveBeenCalledWith("/attempts/att-1/cancel/", {
            reason: "Admin cancelled",
        });
        expect(res).toEqual(mockCancelled);
    });

    it("evaluateDescriptive posts to /attempts/:id/items/:itemId/evaluate/", async () => {
        const mockEval = {
            evaluation_state: "CORRECT",
            marks_awarded: "5.0000",
        };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockEval });

        const res = await attemptsApi.evaluateDescriptive("att-1", "item-1", {
            evaluation_state: "CORRECT",
            marks_awarded: "5.0000",
        });
        expect(apiClient.post).toHaveBeenCalledWith(
            "/attempts/att-1/items/item-1/evaluate/",
            {
                evaluation_state: "CORRECT",
                marks_awarded: "5.0000",
            },
        );
        expect(res).toEqual(mockEval);
    });

    it("getAttemptReview fetches student review data", async () => {
        const mockReview = {
            id: "att-1",
            student_id: "stu-1",
            status: "EVALUATED",
            result_status: "FINAL",
            items: [],
            result: null,
        };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockReview });

        const res = await attemptsApi.getAttemptReview("att-1");
        expect(apiClient.get).toHaveBeenCalledWith("/attempts/att-1/review/");
        expect(res).toEqual(mockReview);
    });
});
