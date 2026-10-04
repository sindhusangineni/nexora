import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import { questionBankApi } from "../api/questionBankApi";
import type {
    QuestionCreatePayload,
    QuestionFilterParams,
    QuestionVersionCreatePayload,
    QuestionVersionFilterParams,
    QuestionVersionPatchPayload,
} from "../types/questionBank.types";

export const questionBankKeys = {
    all: ["question-bank"] as const,
    questions: (params?: QuestionFilterParams) =>
        ["question-bank", "questions", params] as const,
    question: (id: string) => ["question-bank", "question", id] as const,
    versions: (questionId: string, params?: QuestionVersionFilterParams) =>
        ["question-bank", "versions", questionId, params] as const,
    version: (questionId: string, versionId: string) =>
        ["question-bank", "version", questionId, versionId] as const,
};

export function useQuestions(params?: QuestionFilterParams) {
    return useQuery({
        queryKey: questionBankKeys.questions(params),
        queryFn: () => questionBankApi.listQuestions(params),
    });
}

export function useQuestion(questionId: string) {
    return useQuery({
        queryKey: questionBankKeys.question(questionId),
        queryFn: () => questionBankApi.getQuestion(questionId),
        enabled: Boolean(questionId),
    });
}

export function useQuestionVersions(
    questionId: string,
    params?: QuestionVersionFilterParams,
) {
    return useQuery({
        queryKey: questionBankKeys.versions(questionId, params),
        queryFn: () => questionBankApi.listQuestionVersions(questionId, params),
        enabled: Boolean(questionId),
    });
}

export function useQuestionVersion(questionId: string, versionId: string) {
    return useQuery({
        queryKey: questionBankKeys.version(questionId, versionId),
        queryFn: () => questionBankApi.getQuestionVersion(questionId, versionId),
        enabled: Boolean(questionId && versionId),
    });
}

export function useCreateQuestion() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: QuestionCreatePayload) =>
            questionBankApi.createQuestion(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "questions"],
            });
        },
    });
}

export function useCreateQuestionVersion(questionId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: QuestionVersionCreatePayload) =>
            questionBankApi.createQuestionVersion(questionId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: questionBankKeys.question(questionId),
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "versions", questionId],
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "questions"],
            });
        },
    });
}

export function useUpdateDraftVersion(questionId: string, versionId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: QuestionVersionPatchPayload) =>
            questionBankApi.updateDraftVersion(questionId, versionId, payload),
        onSuccess: (updated) => {
            queryClient.setQueryData(
                questionBankKeys.version(questionId, versionId),
                updated,
            );
            queryClient.invalidateQueries({
                queryKey: questionBankKeys.question(questionId),
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "versions", questionId],
            });
        },
    });
}

export function useSubmitReview(questionId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (versionId: string) =>
            questionBankApi.submitReview(questionId, versionId),
        onSuccess: (updated, versionId) => {
            queryClient.setQueryData(
                questionBankKeys.version(questionId, versionId),
                updated,
            );
            queryClient.invalidateQueries({
                queryKey: questionBankKeys.question(questionId),
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "versions", questionId],
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "questions"],
            });
        },
    });
}

export function useApproveVersion(questionId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (versionId: string) =>
            questionBankApi.approveVersion(questionId, versionId),
        onSuccess: (updated, versionId) => {
            queryClient.setQueryData(
                questionBankKeys.version(questionId, versionId),
                updated,
            );
            queryClient.invalidateQueries({
                queryKey: questionBankKeys.question(questionId),
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "versions", questionId],
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "questions"],
            });
        },
    });
}

export function usePublishVersion(questionId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (versionId: string) =>
            questionBankApi.publishVersion(questionId, versionId),
        onSuccess: (updated, versionId) => {
            queryClient.setQueryData(
                questionBankKeys.version(questionId, versionId),
                updated,
            );
            queryClient.invalidateQueries({
                queryKey: questionBankKeys.question(questionId),
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "versions", questionId],
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "questions"],
            });
        },
    });
}

export function useArchiveVersion(questionId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (versionId: string) =>
            questionBankApi.archiveVersion(questionId, versionId),
        onSuccess: (updated, versionId) => {
            queryClient.setQueryData(
                questionBankKeys.version(questionId, versionId),
                updated,
            );
            queryClient.invalidateQueries({
                queryKey: questionBankKeys.question(questionId),
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "versions", questionId],
            });
            queryClient.invalidateQueries({
                queryKey: ["question-bank", "questions"],
            });
        },
    });
}
