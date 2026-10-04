import { apiClient } from "@/lib/api";
import type {
    Assessment,
    AssessmentCreatePayload,
    AssessmentPaper,
    AssessmentSection,
    AssessmentUpdatePayload,
    RuleCreatePayload,
    SectionCreatePayload,
    SelectionRule,
} from "../types/assessment.types";

export const assessmentApi = {
    // Assessment Definitions & Lifecycle
    async listAssessments(): Promise<Assessment[]> {
        const response = await apiClient.get<Assessment[]>("/assessment/assessments/");
        return response.data;
    },

    async getAssessment(assessmentId: string): Promise<Assessment> {
        const response = await apiClient.get<Assessment>(`/assessment/assessments/${assessmentId}/`);
        return response.data;
    },

    async createAssessment(payload: AssessmentCreatePayload): Promise<Assessment> {
        const response = await apiClient.post<Assessment>("/assessment/assessments/", payload);
        return response.data;
    },

    async updateAssessment(
        assessmentId: string,
        payload: AssessmentUpdatePayload,
    ): Promise<Assessment> {
        const response = await apiClient.patch<Assessment>(
            `/assessment/assessments/${assessmentId}/`,
            payload,
        );
        return response.data;
    },

    async publishAssessment(assessmentId: string): Promise<Assessment> {
        const response = await apiClient.post<Assessment>(
            `/assessment/assessments/${assessmentId}/publish/`,
        );
        return response.data;
    },

    async archiveAssessment(assessmentId: string): Promise<Assessment> {
        const response = await apiClient.post<Assessment>(
            `/assessment/assessments/${assessmentId}/archive/`,
        );
        return response.data;
    },

    // Sections
    async listSections(assessmentId: string): Promise<AssessmentSection[]> {
        const response = await apiClient.get<AssessmentSection[]>(
            `/assessment/assessments/${assessmentId}/sections/`,
        );
        return response.data;
    },

    async createSection(
        assessmentId: string,
        payload: SectionCreatePayload,
    ): Promise<AssessmentSection> {
        const response = await apiClient.post<AssessmentSection>(
            `/assessment/assessments/${assessmentId}/sections/`,
            payload,
        );
        return response.data;
    },

    async deleteSection(sectionId: string): Promise<void> {
        await apiClient.delete(`/assessment/sections/${sectionId}/`);
    },

    // Selection Rules
    async listRules(assessmentId: string): Promise<SelectionRule[]> {
        const response = await apiClient.get<SelectionRule[]>(
            `/assessment/assessments/${assessmentId}/rules/`,
        );
        return response.data;
    },

    async createRule(
        assessmentId: string,
        payload: RuleCreatePayload,
    ): Promise<SelectionRule> {
        const response = await apiClient.post<SelectionRule>(
            `/assessment/assessments/${assessmentId}/rules/`,
            payload,
        );
        return response.data;
    },

    async deleteRule(ruleId: string): Promise<void> {
        await apiClient.delete(`/assessment/rules/${ruleId}/`);
    },

    // Paper Generation & Retrieval
    async generatePaper(assessmentId: string): Promise<AssessmentPaper> {
        const response = await apiClient.post<AssessmentPaper>(
            `/assessment/assessments/${assessmentId}/generate-paper/`,
        );
        return response.data;
    },

    async getPaper(paperId: string): Promise<AssessmentPaper> {
        const response = await apiClient.get<AssessmentPaper>(
            `/assessment/papers/${paperId}/`,
        );
        return response.data;
    },
};
