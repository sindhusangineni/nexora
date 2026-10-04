import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { learningApi } from "../api/learningApi";
import type {
    ChapterListParams,
    CreateChapterPayload,
    CreateDomainPayload,
    CreateSubjectPayload,
    CreateTopicPayload,
    CurriculumListParams,
    SubjectListParams,
    TopicListParams,
    UpdateChapterPayload,
    UpdateDomainPayload,
    UpdateSubjectPayload,
    UpdateTopicPayload,
} from "../types/learning.types";

export const learningKeys = {
    all: ["learning"] as const,
    domains: (params?: CurriculumListParams) => ["learning", "domains", params] as const,
    domain: (id?: string) => ["learning", "domain", id] as const,
    subjects: (params?: SubjectListParams) => ["learning", "subjects", params] as const,
    subject: (id?: string) => ["learning", "subject", id] as const,
    chapters: (params?: ChapterListParams) => ["learning", "chapters", params] as const,
    chapter: (id?: string) => ["learning", "chapter", id] as const,
    topics: (params?: TopicListParams) => ["learning", "topics", params] as const,
    topic: (id?: string) => ["learning", "topic", id] as const,
};

// --- Domain Queries ---
export function useDomains(params?: CurriculumListParams, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.domains(params),
        queryFn: () => learningApi.getDomains(params),
        enabled: options?.enabled ?? true,
    });
}

export function useDomain(id?: string, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.domain(id),
        queryFn: () => learningApi.getDomain(id!),
        enabled: Boolean(id) && (options?.enabled ?? true),
    });
}

// --- Subject Queries ---
export function useSubjects(params?: SubjectListParams, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.subjects(params),
        queryFn: () => learningApi.getSubjects(params),
        enabled: options?.enabled ?? true,
    });
}

export function useSubject(id?: string, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.subject(id),
        queryFn: () => learningApi.getSubject(id!),
        enabled: Boolean(id) && (options?.enabled ?? true),
    });
}

// --- Chapter Queries ---
export function useChapters(params?: ChapterListParams, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.chapters(params),
        queryFn: () => learningApi.getChapters(params),
        enabled: options?.enabled ?? true,
    });
}

export function useChapter(id?: string, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.chapter(id),
        queryFn: () => learningApi.getChapter(id!),
        enabled: Boolean(id) && (options?.enabled ?? true),
    });
}

// --- Topic Queries ---
export function useTopics(params?: TopicListParams, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.topics(params),
        queryFn: () => learningApi.getTopics(params),
        enabled: options?.enabled ?? true,
    });
}

export function useTopic(id?: string, options?: { enabled?: boolean }) {
    return useQuery({
        queryKey: learningKeys.topic(id),
        queryFn: () => learningApi.getTopic(id!),
        enabled: Boolean(id) && (options?.enabled ?? true),
    });
}

// --- Domain Mutations ---
export function useCreateDomain() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateDomainPayload) => learningApi.createDomain(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["learning", "domains"] });
        },
    });
}

export function useUpdateDomain() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: UpdateDomainPayload }) =>
            learningApi.updateDomain(id, payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "domains"] });
            queryClient.invalidateQueries({ queryKey: learningKeys.domain(variables.id) });
        },
    });
}

export function useDeleteDomain() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => learningApi.deleteDomain(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["learning", "domains"] });
            queryClient.invalidateQueries({ queryKey: ["learning", "subjects"] });
        },
    });
}

// --- Subject Mutations ---
export function useCreateSubject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateSubjectPayload) => learningApi.createSubject(payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "subjects"] });
            queryClient.invalidateQueries({
                queryKey: learningKeys.subjects({ domain: variables.domain }),
            });
        },
    });
}

export function useUpdateSubject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: UpdateSubjectPayload }) =>
            learningApi.updateSubject(id, payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "subjects"] });
            queryClient.invalidateQueries({ queryKey: learningKeys.subject(variables.id) });
        },
    });
}

export function useDeleteSubject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => learningApi.deleteSubject(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["learning", "subjects"] });
            queryClient.invalidateQueries({ queryKey: ["learning", "chapters"] });
        },
    });
}

// --- Chapter Mutations ---
export function useCreateChapter() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateChapterPayload) => learningApi.createChapter(payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "chapters"] });
            queryClient.invalidateQueries({
                queryKey: learningKeys.chapters({ subject: variables.subject }),
            });
        },
    });
}

export function useUpdateChapter() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: UpdateChapterPayload }) =>
            learningApi.updateChapter(id, payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "chapters"] });
            queryClient.invalidateQueries({ queryKey: learningKeys.chapter(variables.id) });
        },
    });
}

export function useDeleteChapter() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => learningApi.deleteChapter(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["learning", "chapters"] });
            queryClient.invalidateQueries({ queryKey: ["learning", "topics"] });
        },
    });
}

// --- Topic Mutations ---
export function useCreateTopic() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateTopicPayload) => learningApi.createTopic(payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "topics"] });
            queryClient.invalidateQueries({
                queryKey: learningKeys.topics({ chapter: variables.chapter }),
            });
        },
    });
}

export function useUpdateTopic() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: UpdateTopicPayload }) =>
            learningApi.updateTopic(id, payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["learning", "topics"] });
            queryClient.invalidateQueries({ queryKey: learningKeys.topic(variables.id) });
        },
    });
}

export function useDeleteTopic() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => learningApi.deleteTopic(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["learning", "topics"] });
        },
    });
}
