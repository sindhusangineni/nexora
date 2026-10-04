/**
 * Nexora - Attempts API Client
 * Phase 3D: Student Attempt Experience, Timer, Responses, Submission & History
 */

import { apiClient } from "@/lib/api/client";
import type {
    AttemptDelivery,
    AttemptHistoryResponse,
    AttemptResponseDelivery,
    AttemptResult,
    AttemptReview,
    AttemptStatus,
    CancelAttemptPayload,
    DeliveryQuestionVersion,
    EvaluateDescriptivePayload,
    SaveResponsePayload,
    StartAttemptPayload,
    StudentAttemptReviewResponse,
} from "../types/attempt.types";
import type {
    Assessment,
    AssessmentPaper,
    AssessmentSection,
} from "@/features/assessment/types/assessment.types";

export const attemptsApi = {
    /**
     * Retrieve authenticated student's attempt history.
     */
    async getAttemptHistory(params?: {
        status?: AttemptStatus;
        page?: number;
        page_size?: number;
    }): Promise<AttemptHistoryResponse> {
        const queryParams = new URLSearchParams();
        if (params?.status) queryParams.set("status", params.status);
        if (params?.page) queryParams.set("page", params.page.toString());
        if (params?.page_size) queryParams.set("page_size", params.page_size.toString());

        const query = queryParams.toString();
        const url = query ? `/attempts/?${query}` : "/attempts/";
        const response = await apiClient.get<AttemptHistoryResponse>(url);
        return response.data;
    },

    /**
     * Start a new attempt or idempotently retrieve active attempt for an assessment paper.
     */
    async startAttempt(payload: StartAttemptPayload): Promise<AttemptDelivery> {
        const response = await apiClient.post<AttemptDelivery>("/attempts/", payload);
        return response.data;
    },

    /**
     * Retrieve delivery-safe attempt data. Only student owner or superadmin can access.
     */
    async getAttempt(attemptId: string): Promise<AttemptDelivery> {
        const response = await apiClient.get<AttemptDelivery>(`/attempts/${attemptId}/`);
        return response.data;
    },

    /**
     * Save/record student answer on an active AttemptItem.
     */
    async saveResponse(
        attemptId: string,
        itemId: string,
        payload: SaveResponsePayload,
    ): Promise<AttemptResponseDelivery> {
        const response = await apiClient.put<AttemptResponseDelivery>(
            `/attempts/${attemptId}/items/${itemId}/response/`,
            payload,
        );
        return response.data;
    },

    /**
     * Reset a previously answered item back to UNANSWERED.
     */
    async clearResponse(
        attemptId: string,
        itemId: string,
    ): Promise<AttemptResponseDelivery> {
        const response = await apiClient.delete<AttemptResponseDelivery>(
            `/attempts/${attemptId}/items/${itemId}/response/`,
        );
        return response.data;
    },

    /**
     * Submit an attempt. Evaluates synchronously if all items are objective.
     */
    async submitAttempt(attemptId: string): Promise<AttemptDelivery> {
        const response = await apiClient.post<AttemptDelivery>(
            `/attempts/${attemptId}/submit/`,
        );
        return response.data;
    },

    /**
     * Retrieve scorecard result for an attempt.
     */
    async getAttemptResult(attemptId: string): Promise<AttemptResult> {
        const response = await apiClient.get<AttemptResult>(
            `/attempts/${attemptId}/result/`,
        );
        return response.data;
    },

    /**
     * Retrieve sanitized question content for student display.
     */
    async getStudentQuestionVersion(
        questionId: string,
        versionId: string,
    ): Promise<DeliveryQuestionVersion> {
        const response = await apiClient.get<DeliveryQuestionVersion>(
            `/question-bank/questions/${questionId}/versions/${versionId}/`,
        );
        return response.data;
    },

    /**
     * Retrieve paper snapshot to map sections and question versions.
     */
    async getAssessmentPaper(paperId: string): Promise<AssessmentPaper> {
        const response = await apiClient.get<AssessmentPaper>(
            `/assessment/papers/${paperId}/`,
        );
        return response.data;
    },

    /**
     * Retrieve assessment metadata.
     */
    async getAssessment(assessmentId: string): Promise<Assessment> {
        const response = await apiClient.get<Assessment>(
            `/assessment/assessments/${assessmentId}/`,
        );
        return response.data;
    },

    /**
     * Retrieve assessment sections.
     */
    async getAssessmentSections(assessmentId: string): Promise<AssessmentSection[]> {
        const response = await apiClient.get<{ results: AssessmentSection[] } | AssessmentSection[]>(
            `/assessment/sections/?assessment_id=${assessmentId}`,
        );
        if (Array.isArray(response.data)) {
            return response.data;
        }
        return response.data.results || [];
    },

    /**
     * Retrieve student attempt review with solutions and scorecard.
     */
    async getAttemptReview(attemptId: string): Promise<StudentAttemptReviewResponse> {
        const response = await apiClient.get<StudentAttemptReviewResponse>(
            `/attempts/${attemptId}/review/`,
        );
        return response.data;
    },

    /**
     * Superadmin full review of an attempt.
     */
    async reviewAttempt(attemptId: string): Promise<AttemptReview> {
        const response = await apiClient.get<AttemptReview>(
            `/attempts/${attemptId}/review/`,
        );
        return response.data;
    },

    /**
     * Superadmin cancellation of an active/submitted attempt.
     */
    async cancelAttempt(
        attemptId: string,
        payload: CancelAttemptPayload,
    ): Promise<AttemptDelivery> {
        const response = await apiClient.post<AttemptDelivery>(
            `/attempts/${attemptId}/cancel/`,
            payload,
        );
        return response.data;
    },

    /**
     * Superadmin evaluation of descriptive response item.
     */
    async evaluateDescriptive(
        attemptId: string,
        itemId: string,
        payload: EvaluateDescriptivePayload,
    ): Promise<{ evaluation_state: string; marks_awarded: string | null }> {
        const response = await apiClient.post<{
            evaluation_state: string;
            marks_awarded: string | null;
        }>(`/attempts/${attemptId}/items/${itemId}/evaluate/`, payload);
        return response.data;
    },
};
