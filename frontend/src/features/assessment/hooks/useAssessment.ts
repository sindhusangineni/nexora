import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import { assessmentApi } from "../api/assessmentApi";
import type {
    AssessmentCreatePayload,
    AssessmentUpdatePayload,
    RuleCreatePayload,
    SectionCreatePayload,
} from "../types/assessment.types";

export const assessmentKeys = {
    all: ["assessment"] as const,
    assessments: () => ["assessment", "assessments"] as const,
    assessment: (id: string) => ["assessment", "detail", id] as const,
    sections: (assessmentId: string) => ["assessment", "sections", assessmentId] as const,
    rules: (assessmentId: string) => ["assessment", "rules", assessmentId] as const,
    paper: (paperId: string) => ["assessment", "paper", paperId] as const,
};

export function useAssessments() {
    return useQuery({
        queryKey: assessmentKeys.assessments(),
        queryFn: () => assessmentApi.listAssessments(),
    });
}

export function useAssessment(assessmentId: string) {
    return useQuery({
        queryKey: assessmentKeys.assessment(assessmentId),
        queryFn: () => assessmentApi.getAssessment(assessmentId),
        enabled: Boolean(assessmentId),
    });
}

export function useCreateAssessment() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: AssessmentCreatePayload) =>
            assessmentApi.createAssessment(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessments(),
            });
        },
    });
}

export function useUpdateAssessment(assessmentId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: AssessmentUpdatePayload) =>
            assessmentApi.updateAssessment(assessmentId, payload),
        onSuccess: (updated) => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessment(assessmentId),
            });
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessments(),
            });
            queryClient.setQueryData(assessmentKeys.assessment(assessmentId), updated);
        },
    });
}

export function usePublishAssessment() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (assessmentId: string) =>
            assessmentApi.publishAssessment(assessmentId),
        onSuccess: (updated) => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessment(updated.id),
            });
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessments(),
            });
            queryClient.setQueryData(assessmentKeys.assessment(updated.id), updated);
        },
    });
}

export function useArchiveAssessment() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (assessmentId: string) =>
            assessmentApi.archiveAssessment(assessmentId),
        onSuccess: (updated) => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessment(updated.id),
            });
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessments(),
            });
            queryClient.setQueryData(assessmentKeys.assessment(updated.id), updated);
        },
    });
}

export function useAssessmentSections(assessmentId: string) {
    return useQuery({
        queryKey: assessmentKeys.sections(assessmentId),
        queryFn: () => assessmentApi.listSections(assessmentId),
        enabled: Boolean(assessmentId),
    });
}

export function useCreateSection(assessmentId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: SectionCreatePayload) =>
            assessmentApi.createSection(assessmentId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.sections(assessmentId),
            });
        },
    });
}

export function useDeleteSection(assessmentId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (sectionId: string) => assessmentApi.deleteSection(sectionId),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.sections(assessmentId),
            });
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.rules(assessmentId),
            });
        },
    });
}

export function useSelectionRules(assessmentId: string) {
    return useQuery({
        queryKey: assessmentKeys.rules(assessmentId),
        queryFn: () => assessmentApi.listRules(assessmentId),
        enabled: Boolean(assessmentId),
    });
}

export function useCreateSelectionRule(assessmentId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: RuleCreatePayload) =>
            assessmentApi.createRule(assessmentId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.rules(assessmentId),
            });
        },
    });
}

export function useDeleteSelectionRule(assessmentId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (ruleId: string) => assessmentApi.deleteRule(ruleId),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.rules(assessmentId),
            });
        },
    });
}

export function useGeneratePaper(assessmentId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: () => assessmentApi.generatePaper(assessmentId),
        onSuccess: (paper) => {
            queryClient.setQueryData(assessmentKeys.paper(paper.id), paper);
            queryClient.invalidateQueries({
                queryKey: assessmentKeys.assessment(assessmentId),
            });
        },
    });
}

export function useAssessmentPaper(paperId: string) {
    return useQuery({
        queryKey: assessmentKeys.paper(paperId),
        queryFn: () => assessmentApi.getPaper(paperId),
        enabled: Boolean(paperId),
    });
}
