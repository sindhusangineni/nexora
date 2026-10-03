import { apiClient } from "@/lib/api";
import type {
    Chapter,
    ChapterListParams,
    CreateChapterPayload,
    CreateDomainPayload,
    CreateSubjectPayload,
    CreateTopicPayload,
    CurriculumListParams,
    Domain,
    PaginatedResponse,
    Subject,
    SubjectListParams,
    Topic,
    TopicListParams,
    UpdateChapterPayload,
    UpdateDomainPayload,
    UpdateSubjectPayload,
    UpdateTopicPayload,
} from "../types/learning.types";

function cleanParams(params?: Record<string, unknown>): Record<string, unknown> | undefined {
    if (!params) return undefined;
    const cleaned: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== "") {
            cleaned[key] = value;
        }
    }
    return cleaned;
}

export const learningApi = {
    // Domains
    async getDomains(params?: CurriculumListParams): Promise<PaginatedResponse<Domain>> {
        const response = await apiClient.get<PaginatedResponse<Domain>>("/learning/domains/", {
            params: cleanParams(params as Record<string, unknown>),
        });
        return response.data;
    },

    async getDomain(id: string): Promise<Domain> {
        const response = await apiClient.get<Domain>(`/learning/domains/${id}/`);
        return response.data;
    },

    async createDomain(payload: CreateDomainPayload): Promise<Domain> {
        const response = await apiClient.post<Domain>("/learning/domains/", payload);
        return response.data;
    },

    async updateDomain(id: string, payload: UpdateDomainPayload): Promise<Domain> {
        const response = await apiClient.patch<Domain>(`/learning/domains/${id}/`, payload);
        return response.data;
    },

    async deleteDomain(id: string): Promise<void> {
        await apiClient.delete(`/learning/domains/${id}/`);
    },

    // Subjects
    async getSubjects(params?: SubjectListParams): Promise<PaginatedResponse<Subject>> {
        const response = await apiClient.get<PaginatedResponse<Subject>>("/learning/subjects/", {
            params: cleanParams(params as Record<string, unknown>),
        });
        return response.data;
    },

    async getSubject(id: string): Promise<Subject> {
        const response = await apiClient.get<Subject>(`/learning/subjects/${id}/`);
        return response.data;
    },

    async createSubject(payload: CreateSubjectPayload): Promise<Subject> {
        const response = await apiClient.post<Subject>("/learning/subjects/", payload);
        return response.data;
    },

    async updateSubject(id: string, payload: UpdateSubjectPayload): Promise<Subject> {
        const response = await apiClient.patch<Subject>(`/learning/subjects/${id}/`, payload);
        return response.data;
    },

    async deleteSubject(id: string): Promise<void> {
        await apiClient.delete(`/learning/subjects/${id}/`);
    },

    // Chapters
    async getChapters(params?: ChapterListParams): Promise<PaginatedResponse<Chapter>> {
        const response = await apiClient.get<PaginatedResponse<Chapter>>("/learning/chapters/", {
            params: cleanParams(params as Record<string, unknown>),
        });
        return response.data;
    },

    async getChapter(id: string): Promise<Chapter> {
        const response = await apiClient.get<Chapter>(`/learning/chapters/${id}/`);
        return response.data;
    },

    async createChapter(payload: CreateChapterPayload): Promise<Chapter> {
        const response = await apiClient.post<Chapter>("/learning/chapters/", payload);
        return response.data;
    },

    async updateChapter(id: string, payload: UpdateChapterPayload): Promise<Chapter> {
        const response = await apiClient.patch<Chapter>(`/learning/chapters/${id}/`, payload);
        return response.data;
    },

    async deleteChapter(id: string): Promise<void> {
        await apiClient.delete(`/learning/chapters/${id}/`);
    },

    // Topics
    async getTopics(params?: TopicListParams): Promise<PaginatedResponse<Topic>> {
        const response = await apiClient.get<PaginatedResponse<Topic>>("/learning/topics/", {
            params: cleanParams(params as Record<string, unknown>),
        });
        return response.data;
    },

    async getTopic(id: string): Promise<Topic> {
        const response = await apiClient.get<Topic>(`/learning/topics/${id}/`);
        return response.data;
    },

    async createTopic(payload: CreateTopicPayload): Promise<Topic> {
        const response = await apiClient.post<Topic>("/learning/topics/", payload);
        return response.data;
    },

    async updateTopic(id: string, payload: UpdateTopicPayload): Promise<Topic> {
        const response = await apiClient.patch<Topic>(`/learning/topics/${id}/`, payload);
        return response.data;
    },

    async deleteTopic(id: string): Promise<void> {
        await apiClient.delete(`/learning/topics/${id}/`);
    },
};
