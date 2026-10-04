export type AssessmentType = "PRACTICE" | "REVISION" | "MOCK" | "CUSTOM";

export type AssessmentStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export type ScopeType = "DOMAIN" | "SUBJECT" | "CHAPTER" | "TOPIC";

export type QuestionType =
    | "MCQ"
    | "MULTIPLE_SELECT"
    | "TRUE_FALSE"
    | "ASSERTION_REASON"
    | "MATCH_FOLLOWING"
    | "DESCRIPTIVE";

export type Difficulty = "EASY" | "MEDIUM" | "HARD";

export type PaperStatus = "GENERATED";

export type ScoreFloorPolicy =
    | "UNRESTRICTED"
    | "ZERO_FLOOR_TOTAL"
    | "ZERO_FLOOR_SECTION";

export interface Assessment {
    id: string;
    title: string;
    description: string;
    type: AssessmentType;
    status: AssessmentStatus;
    duration_seconds: number;
    marks_per_question: string;
    penalty_per_question: string;
    created_at: string;
    updated_at: string;
}

export interface AssessmentCreatePayload {
    title: string;
    description?: string;
    type?: AssessmentType;
    duration_seconds?: number;
    marks_per_question?: string;
    penalty_per_question?: string;
}

export interface AssessmentUpdatePayload {
    title?: string;
    description?: string;
    type?: AssessmentType;
    duration_seconds?: number;
    marks_per_question?: string;
    penalty_per_question?: string;
}

export interface AssessmentSection {
    id: string;
    assessment_id: string;
    title: string;
    description: string;
    position: number;
    created_at: string;
    updated_at: string;
}

export interface SectionCreatePayload {
    title: string;
    description?: string;
    position: number;
}

export interface SelectionRule {
    id: string;
    assessment_id: string;
    assessment_section_id: string | null;
    scope_type: ScopeType;
    scope_id: string;
    question_type: QuestionType | null;
    difficulty: Difficulty | null;
    question_count: number;
    position: number;
    created_at: string;
    updated_at: string;
}

export interface RuleCreatePayload {
    assessment_section_id?: string | null;
    scope_type: ScopeType;
    scope_id: string;
    question_type?: QuestionType | null;
    difficulty?: Difficulty | null;
    question_count: number;
    position: number;
}

export interface AssessmentPaperItem {
    id: string;
    paper_id: string;
    question_id: string;
    question_version_id: string;
    assessment_section_id: string | null;
    presentation_order: number;
    allocated_marks: string;
    allocated_penalty: string;
    created_at: string;
}

export interface AssessmentPaper {
    id: string;
    assessment_id: string;
    status: PaperStatus;
    duration_seconds: number;
    marks_per_question: string;
    penalty_per_question: string;
    created_at: string;
    items: AssessmentPaperItem[];
}
