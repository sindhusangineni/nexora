/**
 * Nexora - Attempts Domain Types
 * Phase 3D: Student Attempt Experience, Timer, Responses, Submission & History
 */

export type AttemptStatus = "IN_PROGRESS" | "SUBMITTED" | "EVALUATED" | "CANCELLED";

export type SubmissionReason = "MANUAL" | "TIMEOUT" | "ADMIN_FORCED";

export type ScoreFloorPolicy = "UNRESTRICTED" | "ZERO_FLOOR_TOTAL" | "ZERO_FLOOR_SECTION";

export type AnswerState = "UNANSWERED" | "ANSWERED";

export type EvaluationState =
    | "UNATTEMPTED"
    | "CORRECT"
    | "INCORRECT"
    | "PARTIALLY_CORRECT"
    | "PENDING_EVALUATION";

export type AttemptResultStatus = "PENDING" | "FINAL" | "VOID";

export const AssertionReasonResponseEnum = {
    BOTH_TRUE_REASON_CORRECT: "BOTH_TRUE_REASON_CORRECT",
    BOTH_TRUE_REASON_NOT_CORRECT: "BOTH_TRUE_REASON_NOT_CORRECT",
    ASSERTION_TRUE_REASON_FALSE: "ASSERTION_TRUE_REASON_FALSE",
    ASSERTION_FALSE_REASON_FALSE: "ASSERTION_FALSE_REASON_FALSE",
} as const;

export type AssertionReasonResponseType =
    (typeof AssertionReasonResponseEnum)[keyof typeof AssertionReasonResponseEnum];

export interface AttemptItemChoice {
    id: string;
    choice_id: string;
    presented_position: number;
}

export interface SelectedMatch {
    left_item_id: string;
    right_item_id: string;
}

export interface AttemptResponseDelivery {
    id: string;
    answer_state: AnswerState;
    boolean_response: boolean | null;
    assertion_reason_response: string | null;
    text_response: string | null;
    selected_choice_ids: string[];
    selected_matches: SelectedMatch[];
}

export interface AttemptItemDelivery {
    id: string; // AttemptItem UUID
    paper_item_id: string;
    assessment_section_id: string | null;
    presentation_order: number;
    allocated_marks: string;
    allocated_penalty: string;
    choices: AttemptItemChoice[];
    response: AttemptResponseDelivery;
}

export interface AttemptDelivery {
    id: string;
    student_id: string;
    assessment_paper_id: string;
    attempt_number: number;
    duration_seconds: number;
    started_at: string;
    expires_at: string;
    submitted_at: string | null;
    status: AttemptStatus;
    items: AttemptItemDelivery[];
}

export interface AttemptSectionResult {
    id: string;
    assessment_section_id: string;
    section_title_snapshot: string;
    section_name?: string;
    section_order_snapshot: number;
    score: string;
    maximum_score: string;
    percentage?: string;
    question_count?: number;
    attempted_questions: number;
    correct_questions: number;
    incorrect_questions: number;
    partially_correct_questions: number;
    unanswered_questions: number;
    pending_evaluation_questions: number;
}

export interface AttemptResult {
    id: string;
    attempt_id: string;
    assessment_paper_id?: string;
    attempt_number?: number;
    attempt_status?: AttemptStatus;
    result_status?: AttemptResultStatus;
    submission_reason?: SubmissionReason | null;
    started_at?: string;
    submitted_at?: string | null;
    status: AttemptResultStatus;
    score: string;
    maximum_score: string;
    percentage: string;
    total_questions: number;
    attempted_questions: number;
    correct_questions: number;
    incorrect_questions: number;
    partially_correct_questions: number;
    unanswered_questions: number;
    pending_evaluation_questions: number;
    finalized_at: string | null;
    section_results: AttemptSectionResult[];
}

export interface QuestionTaxonomy {
    domain?: string;
    subject?: string;
    chapter?: string;
    topic?: string;
}

export interface QuestionReviewItemChoice {
    id: string;
    text: string;
    position: number;
    is_correct?: boolean | null;
}

export interface CandidateAnswer {
    selected_choice_id?: string | null;
    selected_choice_ids?: string[];
    boolean_response?: boolean | null;
    assertion_reason_response?: string | null;
    matches?: Array<{ left_item_id: string; right_item_id: string }>;
    text_response?: string | null;
    [key: string]: unknown;
}

export interface CorrectAnswer {
    correct_choice_id?: string;
    correct_choice_ids?: string[];
    correct_boolean?: boolean;
    correct_relationship?: string;
    correct_matches?: Array<{ left_item_id: string; right_item_id: string }>;
    model_answer?: string;
    [key: string]: unknown;
}

export interface StudentQuestionReviewItem {
    id: string;
    paper_item_id: string;
    assessment_section_id: string | null;
    section_name: string;
    question_id: string;
    question_version_id: string;
    question_number: number;
    presentation_order: number;
    question_type: string;
    question_text: string;
    taxonomy?: QuestionTaxonomy | null;
    allocated_marks: string;
    allocated_penalty: string;
    is_answered: boolean;
    answer_state: AnswerState;
    evaluation_status: EvaluationState;
    marks_awarded: string | null;
    explanation?: string | null;
    choices?: QuestionReviewItemChoice[];
    assertion?: string;
    reason?: string;
    left_items?: Array<{ id: string; text: string; position: number }>;
    right_items?: Array<{ id: string; text: string; position: number }>;
    candidate_answer?: CandidateAnswer | null;
    correct_answer?: CorrectAnswer | null;
}

export interface StudentAttemptReviewResponse {
    id: string;
    student_id: string;
    assessment_paper_id: string;
    attempt_number: number;
    status: AttemptStatus;
    result_status: AttemptResultStatus;
    submission_reason: SubmissionReason | null;
    duration_seconds: number;
    started_at: string;
    submitted_at: string | null;
    items: StudentQuestionReviewItem[];
    result: AttemptResult | null;
}

export interface StartAttemptPayload {
    assessment_paper_id: string;
}

export interface SaveResponsePayload {
    question_type?: string;
    choice_id?: string | null;
    selected_choice_ids?: string[];
    boolean_response?: boolean | null;
    assertion_reason_response?: string | null;
    match_pairs?: { left_item_id: string; right_item_id: string }[];
    text_response?: string | null;
}

export interface CancelAttemptPayload {
    reason: string;
}

export interface EvaluateDescriptivePayload {
    evaluation_state: EvaluationState;
    marks_awarded?: string | null;
    marks_deducted?: string | null;
    evaluation_comments?: string | null;
}

export interface AttemptEvaluationReview {
    id: string;
    evaluation_state: EvaluationState;
    marks_awarded: string | null;
    marks_deducted: string | null;
    net_marks: string | null;
    evaluator_id: string | null;
    evaluated_at: string | null;
    evaluation_comments: string | null;
}

export interface AttemptItemReview {
    id: string;
    paper_item_id: string;
    assessment_section_id: string | null;
    question_id: string;
    question_version_id: string;
    presentation_order: number;
    allocated_marks: string;
    allocated_penalty: string;
    response: AttemptResponseDelivery;
    evaluation: AttemptEvaluationReview | null;
}

export interface AttemptReview {
    id: string;
    student_id: string;
    assessment_paper_id: string;
    attempt_number: number;
    duration_seconds: number;
    started_at: string;
    expires_at: string;
    submitted_at: string | null;
    submission_reason: SubmissionReason | null;
    status: AttemptStatus;
    cancelled_at: string | null;
    cancelled_by: string | null;
    cancellation_reason: string | null;
    items: AttemptItemReview[];
    result: AttemptResult | null;
}

/**
 * Question version student delivery data representation
 */
export interface DeliveryChoice {
    id: string;
    text: string;
    position: number;
}

export interface DeliveryMatchItem {
    id: string;
    text: string;
    position: number;
}

export interface DeliveryQuestionVersion {
    id: string;
    question_id: string;
    version_number: number;
    question_type: string;
    difficulty: string;
    text: string;
    content: {
        choices?: DeliveryChoice[];
        assertion?: string;
        reason?: string;
        left_items?: DeliveryMatchItem[];
        right_items?: DeliveryMatchItem[];
        marks?: string;
    };
}

/**
 * Summary representation for student attempt history listing.
 */
export interface AttemptHistoryItem {
    id: string;
    assessment_paper_id: string;
    attempt_number: number;
    status: AttemptStatus;
    started_at: string;
    submitted_at: string | null;
    expires_at: string;
    submission_reason: SubmissionReason | null;
    result_status: AttemptResultStatus | null;
    score: string | null;
    maximum_score: string | null;
    percentage: string | null;
    total_questions: number | null;
    attempted_questions: number | null;
}

export interface AttemptHistoryResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: AttemptHistoryItem[];
}
