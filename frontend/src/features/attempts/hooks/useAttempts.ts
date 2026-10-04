/**
 * Nexora - Attempts TanStack Query Hooks
 * Phase 3D: Student Attempt Experience, Timer, Responses, Submission & History
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { attemptsApi } from "../api/attemptsApi";
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

export const attemptKeys = {
    all: ["attempts"] as const,
    history: (params?: { status?: AttemptStatus; page?: number; page_size?: number }) =>
        [...attemptKeys.all, "history", params] as const,
    detail: (id: string) => [...attemptKeys.all, "detail", id] as const,
    result: (id: string) => [...attemptKeys.all, "result", id] as const,
    review: (id: string) => [...attemptKeys.all, "review", id] as const,
    paper: (paperId: string) => ["assessment-paper", paperId] as const,
    assessment: (id: string) => ["assessment", id] as const,
    sections: (id: string) => ["assessment-sections", id] as const,
    questionVersion: (qId: string, vId: string) =>
        ["question-version", qId, vId] as const,
};

/**
 * Fetch authenticated student's attempt history.
 */
export function useAttemptHistory(params?: {
    status?: AttemptStatus;
    page?: number;
    page_size?: number;
}) {
    return useQuery<AttemptHistoryResponse, Error>({
        queryKey: attemptKeys.history(params),
        queryFn: () => attemptsApi.getAttemptHistory(params),
        staleTime: 1000 * 15, // 15 seconds
    });
}

/**
 * Fetch delivery-safe attempt representation.
 */
export function useAttempt(attemptId: string, options?: { enabled?: boolean }) {
    return useQuery<AttemptDelivery, Error>({
        queryKey: attemptKeys.detail(attemptId),
        queryFn: () => attemptsApi.getAttempt(attemptId),
        enabled: options?.enabled !== false && !!attemptId,
        staleTime: 1000 * 30, // 30 seconds
    });
}

/**
 * Start or resume an assessment attempt.
 */
export function useStartAttempt() {
    const queryClient = useQueryClient();

    return useMutation<AttemptDelivery, Error, StartAttemptPayload>({
        mutationFn: (payload) => attemptsApi.startAttempt(payload),
        onSuccess: (data) => {
            queryClient.setQueryData(attemptKeys.detail(data.id), data);
        },
    });
}

/**
 * Atomically save/update a student answer on an item.
 * Directly patches the item response in cache upon server confirmation.
 */
export function useSaveResponse(attemptId: string) {
    const queryClient = useQueryClient();

    return useMutation<
        AttemptResponseDelivery,
        Error,
        { itemId: string; payload: SaveResponsePayload }
    >({
        mutationFn: ({ itemId, payload }) =>
            attemptsApi.saveResponse(attemptId, itemId, payload),
        onSuccess: (savedResponse, { itemId }) => {
            queryClient.setQueryData<AttemptDelivery>(
                attemptKeys.detail(attemptId),
                (prev) => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        items: prev.items.map((item) =>
                            item.id === itemId
                                ? { ...item, response: savedResponse }
                                : item,
                        ),
                    };
                },
            );
        },
    });
}

/**
 * Reset a response item back to UNANSWERED.
 */
export function useClearResponse(attemptId: string) {
    const queryClient = useQueryClient();

    return useMutation<AttemptResponseDelivery, Error, { itemId: string }>({
        mutationFn: ({ itemId }) => attemptsApi.clearResponse(attemptId, itemId),
        onSuccess: (clearedResponse, { itemId }) => {
            queryClient.setQueryData<AttemptDelivery>(
                attemptKeys.detail(attemptId),
                (prev) => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        items: prev.items.map((item) =>
                            item.id === itemId
                                ? { ...item, response: clearedResponse }
                                : item,
                        ),
                    };
                },
            );
        },
    });
}

/**
 * Submit an attempt.
 */
export function useSubmitAttempt(attemptId: string) {
    const queryClient = useQueryClient();

    return useMutation<AttemptDelivery, Error, void>({
        mutationFn: () => attemptsApi.submitAttempt(attemptId),
        onSuccess: (submittedAttempt) => {
            queryClient.setQueryData(attemptKeys.detail(attemptId), submittedAttempt);
            queryClient.invalidateQueries({ queryKey: attemptKeys.result(attemptId) });
        },
    });
}

/**
 * Fetch attempt scorecard result with auto-polling while status is PENDING.
 */
export function useAttemptResult(
    attemptId: string,
    options?: { enabled?: boolean },
) {
    return useQuery<AttemptResult, Error>({
        queryKey: attemptKeys.result(attemptId),
        queryFn: () => attemptsApi.getAttemptResult(attemptId),
        enabled: options?.enabled !== false && !!attemptId,
        refetchInterval: (query) => {
            // Stop polling once finalized or if in error state
            if (query.state.data?.status === "FINAL") {
                return false;
            }
            if (query.state.data?.status === "PENDING") {
                return 3000; // Poll every 3 seconds while pending evaluation
            }
            return false;
        },
    });
}

/**
 * Fetch paper snapshot details.
 */
export function useAttemptPaper(paperId?: string) {
    return useQuery({
        queryKey: attemptKeys.paper(paperId || ""),
        queryFn: () => attemptsApi.getAssessmentPaper(paperId!),
        enabled: !!paperId,
        staleTime: Infinity, // Papers are immutable snapshots
    });
}

/**
 * Fetch assessment metadata.
 */
export function useAttemptAssessment(assessmentId?: string) {
    return useQuery({
        queryKey: attemptKeys.assessment(assessmentId || ""),
        queryFn: () => attemptsApi.getAssessment(assessmentId!),
        enabled: !!assessmentId,
        staleTime: 1000 * 60 * 5,
    });
}

/**
 * Fetch assessment sections for organizing attempt items.
 */
export function useAttemptSections(assessmentId?: string) {
    return useQuery({
        queryKey: attemptKeys.sections(assessmentId || ""),
        queryFn: () => attemptsApi.getAssessmentSections(assessmentId!),
        enabled: !!assessmentId,
        staleTime: 1000 * 60 * 5,
    });
}

/**
 * Fetch question delivery representation safely.
 */
export function useDeliveryQuestion(questionId?: string, versionId?: string) {
    return useQuery<DeliveryQuestionVersion, Error>({
        queryKey: attemptKeys.questionVersion(questionId || "", versionId || ""),
        queryFn: () => attemptsApi.getStudentQuestionVersion(questionId!, versionId!),
        enabled: !!questionId && !!versionId,
        staleTime: Infinity, // Pinned versions do not change during an attempt
    });
}

/**
 * Hook to retrieve attempt review with scorecard and solutions.
 * For students: returns student-safe review with solutions and scorecard.
 * Automatically polls while result_status is PENDING.
 */
export function useAttemptReview(
    attemptId: string,
    options?: { enabled?: boolean },
) {
    return useQuery<StudentAttemptReviewResponse, Error>({
        queryKey: attemptKeys.review(attemptId),
        queryFn: () => attemptsApi.getAttemptReview(attemptId),
        enabled: options?.enabled !== false && !!attemptId,
        refetchInterval: (query) => {
            if (query.state.data?.result_status === "FINAL") {
                return false;
            }
            if (query.state.data?.result_status === "PENDING") {
                return 4000; // Poll while pending descriptive evaluation
            }
            return false;
        },
    });
}

/**
 * Superadmin hook to review an entire attempt with admin fields and audit trail.
 */
export function useAdminAttemptReview(
    attemptId: string,
    options?: { enabled?: boolean },
) {
    return useQuery<AttemptReview, Error>({
        queryKey: attemptKeys.review(attemptId),
        queryFn: () => attemptsApi.reviewAttempt(attemptId),
        enabled: options?.enabled !== false && !!attemptId,
    });
}

/**
 * Superadmin cancel attempt mutation.
 */
export function useCancelAttempt(attemptId: string) {
    const queryClient = useQueryClient();

    return useMutation<AttemptDelivery, Error, CancelAttemptPayload>({
        mutationFn: (payload) => attemptsApi.cancelAttempt(attemptId, payload),
        onSuccess: (cancelledAttempt) => {
            queryClient.setQueryData(attemptKeys.detail(attemptId), cancelledAttempt);
            queryClient.invalidateQueries({ queryKey: attemptKeys.review(attemptId) });
        },
    });
}

/**
 * Superadmin evaluate descriptive response mutation.
 */
export function useEvaluateDescriptive(attemptId: string) {
    const queryClient = useQueryClient();

    return useMutation<
        { evaluation_state: string; marks_awarded: string | null },
        Error,
        { itemId: string; payload: EvaluateDescriptivePayload }
    >({
        mutationFn: ({ itemId, payload }) =>
            attemptsApi.evaluateDescriptive(attemptId, itemId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: attemptKeys.review(attemptId) });
            queryClient.invalidateQueries({ queryKey: attemptKeys.result(attemptId) });
        },
    });
}
