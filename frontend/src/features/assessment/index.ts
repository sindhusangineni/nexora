// Public API for assessment feature
export { assessmentApi } from "./api/assessmentApi";

export {
    assessmentKeys,
    useAssessments,
    useAssessment,
    useCreateAssessment,
    useUpdateAssessment,
    usePublishAssessment,
    useArchiveAssessment,
    useAssessmentSections,
    useCreateSection,
    useDeleteSection,
    useSelectionRules,
    useCreateSelectionRule,
    useDeleteSelectionRule,
    useGeneratePaper,
    useAssessmentPaper,
} from "./hooks/useAssessment";

export { AssessmentStatusBadge, AssessmentTypeBadge } from "./components/AssessmentStatusBadge";
export { TaxonomySelector } from "./components/TaxonomySelector";
export { SectionManager } from "./components/SectionManager";
export { SelectionRuleEditor } from "./components/SelectionRuleEditor";
export { SelectionRuleList } from "./components/SelectionRuleList";
export { MarkingTimingConfiguration } from "./components/MarkingTimingConfiguration";
export { AssessmentReview } from "./components/AssessmentReview";
export { AssessmentLifecycleActions } from "./components/AssessmentLifecycleActions";
export { PaperPreview } from "./components/PaperPreview";
export { AssessmentForm } from "./components/AssessmentForm";

export type {
    Assessment,
    AssessmentType,
    AssessmentStatus,
    ScopeType,
    QuestionType,
    Difficulty,
    PaperStatus,
    ScoreFloorPolicy,
    AssessmentCreatePayload,
    AssessmentUpdatePayload,
    AssessmentSection,
    SectionCreatePayload,
    SelectionRule,
    RuleCreatePayload,
    AssessmentPaperItem,
    AssessmentPaper,
} from "./types/assessment.types";
