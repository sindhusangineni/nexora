import { apiClient } from "@/lib/api";
import type {
    PaginatedResponse,
    QuestionAdminResponse,
    QuestionCreatePayload,
    QuestionFilterParams,
    QuestionVersionAdminResponse,
    QuestionVersionCreatePayload,
    QuestionVersionFilterParams,
    QuestionVersionPatchPayload,
    QuestionImportPreviewResponse,
    QuestionImportExecuteResponse,
} from "../types/questionBank.types";

export const questionBankApi = {
    async listQuestions(
        params?: QuestionFilterParams,
    ): Promise<PaginatedResponse<QuestionAdminResponse>> {
        const response = await apiClient.get<PaginatedResponse<QuestionAdminResponse>>(
            "/question-bank/questions/",
            { params },
        );
        return response.data;
    },

    async getQuestion(questionId: string): Promise<QuestionAdminResponse> {
        const response = await apiClient.get<QuestionAdminResponse>(
            `/question-bank/questions/${questionId}/`,
        );
        return response.data;
    },

    async createQuestion(
        payload: QuestionCreatePayload,
    ): Promise<QuestionAdminResponse> {
        const response = await apiClient.post<QuestionAdminResponse>(
            "/question-bank/questions/",
            payload,
        );
        return response.data;
    },

    async listQuestionVersions(
        questionId: string,
        params?: QuestionVersionFilterParams,
    ): Promise<PaginatedResponse<QuestionVersionAdminResponse>> {
        const response = await apiClient.get<
            PaginatedResponse<QuestionVersionAdminResponse>
        >(`/question-bank/questions/${questionId}/versions/`, { params });
        return response.data;
    },

    async getQuestionVersion(
        questionId: string,
        versionId: string,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.get<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/${versionId}/`,
        );
        return response.data;
    },

    async createQuestionVersion(
        questionId: string,
        payload: QuestionVersionCreatePayload,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.post<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/`,
            payload,
        );
        return response.data;
    },

    async updateDraftVersion(
        questionId: string,
        versionId: string,
        payload: QuestionVersionPatchPayload,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.patch<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/${versionId}/`,
            payload,
        );
        return response.data;
    },

    async submitReview(
        questionId: string,
        versionId: string,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.post<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/${versionId}/submit-review/`,
        );
        return response.data;
    },

    async approveVersion(
        questionId: string,
        versionId: string,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.post<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/${versionId}/approve/`,
        );
        return response.data;
    },

    async publishVersion(
        questionId: string,
        versionId: string,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.post<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/${versionId}/publish/`,
        );
        return response.data;
    },

    async archiveVersion(
        questionId: string,
        versionId: string,
    ): Promise<QuestionVersionAdminResponse> {
        const response = await apiClient.post<QuestionVersionAdminResponse>(
            `/question-bank/questions/${questionId}/versions/${versionId}/archive/`,
        );
        return response.data;
    },

    async previewImport(file: File): Promise<QuestionImportPreviewResponse> {
        const formData = new FormData();
        formData.append("file", file);
        const response = await apiClient.post<QuestionImportPreviewResponse>(
            "/question-bank/imports/preview/",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            },
        );
        return response.data;
    },

    async executeImport(
        file: File,
        skipDuplicates: boolean = true,
    ): Promise<QuestionImportExecuteResponse> {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("skip_duplicates", String(skipDuplicates));
        const response = await apiClient.post<QuestionImportExecuteResponse>(
            "/question-bank/imports/execute/",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            },
        );
        return response.data;
    },

    async downloadTemplate(): Promise<Blob> {
        const response = await apiClient.get<Blob>(
            "/question-bank/imports/template/",
            {
                responseType: "blob",
            },
        );
        return response.data;
    },
};
