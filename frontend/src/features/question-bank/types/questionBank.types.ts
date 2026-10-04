export type QuestionType =
    | "MCQ"
    | "MULTIPLE_SELECT"
    | "TRUE_FALSE"
    | "ASSERTION_REASON"
    | "MATCH_FOLLOWING"
    | "DESCRIPTIVE";

export type Difficulty = "EASY" | "MEDIUM" | "HARD";

export type QuestionStatus =
    | "DRAFT"
    | "REVIEW"
    | "APPROVED"
    | "PUBLISHED"
    | "ARCHIVED";

export type QuestionSourceType =
    | "ORIGINAL"
    | "UPSC_PREVIOUS_YEAR"
    | "LICENSED"
    | "CONTRIBUTOR"
    | "AI_GENERATED"
    | "IMPORTED";

export type AssertionReasonRelationship =
    | "BOTH_TRUE_REASON_CORRECT"
    | "BOTH_TRUE_REASON_NOT_CORRECT"
    | "ASSERTION_TRUE_REASON_FALSE"
    | "ASSERTION_FALSE_REASON_FALSE";

export interface ChoiceItem {
    id?: string;
    text: string;
    position?: number;
    is_correct?: boolean;
}

export interface TrueFalseContent {
    answer: boolean;
}

export interface AssertionReasonContent {
    assertion: string;
    reason: string;
    correct_relationship: AssertionReasonRelationship;
}

export interface MatchItem {
    id?: string;
    text: string;
    position: number;
}

export interface MatchPair {
    left_position: number;
    right_position: number;
}

export interface MatchFollowingContent {
    left_items: MatchItem[];
    right_items: MatchItem[];
    pairs: MatchPair[];
}

export interface DescriptiveContent {
    marks: number;
    expected_answer: string;
}

export interface QuestionVersionAdminResponse {
    id: string;
    question_id: string;
    version_number: number;
    question_type: QuestionType;
    difficulty: Difficulty;
    status: QuestionStatus;
    text: string;
    explanation?: string;
    source_type?: QuestionSourceType | null;
    source_name?: string | null;
    source_reference?: string | null;
    source_year?: number | null;
    external_question_id?: string | null;
    content: {
        choices?: ChoiceItem[];
        answer?: boolean | null;
        assertion?: string;
        reason?: string;
        correct_relationship?: AssertionReasonRelationship;
        left_items?: MatchItem[];
        right_items?: MatchItem[];
        pairs?: MatchPair[];
        marks?: number;
        expected_answer?: string;
    };
    created_at: string;
    updated_at: string;
}

export interface QuestionVersionStudentResponse {
    id: string;
    question_id: string;
    version_number: number;
    question_type: QuestionType;
    difficulty: Difficulty;
    text: string;
    content: {
        choices?: Array<{ id: string; text: string; position: number }>;
        assertion?: string;
        reason?: string;
        left_items?: Array<{ id: string; text: string; position: number }>;
        right_items?: Array<{ id: string; text: string; position: number }>;
        marks?: number;
    };
}

export type QuestionVersionDelivery = QuestionVersionStudentResponse;

export interface QuestionAdminResponse {
    id: string;
    topic_ids: string[];
    latest_version: QuestionVersionAdminResponse | null;
    published_version: QuestionVersionAdminResponse | null;
    version_count: number;
    created_at: string;
    updated_at: string;
}

export interface QuestionStudentResponse {
    id: string;
    topic_ids: string[];
    published_version: QuestionVersionStudentResponse | null;
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export type QuestionListResponse = PaginatedResponse<QuestionAdminResponse>;

export interface QuestionFilterParams {
    search?: string;
    topic?: string;
    question_type?: QuestionType;
    difficulty?: Difficulty;
    status?: QuestionStatus;
    page?: number;
    page_size?: number;
}

export interface QuestionVersionFilterParams {
    search?: string;
    question_type?: QuestionType;
    difficulty?: Difficulty;
    status?: QuestionStatus;
    page?: number;
    page_size?: number;
}

export interface BaseQuestionCreatePayload {
    question_type: QuestionType;
    text: string;
    difficulty: Difficulty;
    explanation?: string;
    topic_ids?: string[];
    source_type?: QuestionSourceType | null;
    source_name?: string | null;
    source_reference?: string | null;
    source_year?: number | null;
    external_question_id?: string | null;
    choices?: Array<{ text: string; position?: number; is_correct?: boolean }>;
    true_false?: TrueFalseContent;
    assertion_reason?: {
        assertion: string;
        reason: string;
        correct_relationship: AssertionReasonRelationship;
    };
    match_following?: {
        left_items: Array<{ text: string; position?: number }>;
        right_items: Array<{ text: string; position?: number }>;
        pairs: Array<{ left_position: number; right_position: number }>;
    };
    descriptive?: DescriptiveContent;
}

export type QuestionCreatePayload = BaseQuestionCreatePayload;
export type QuestionVersionCreatePayload = BaseQuestionCreatePayload;

export interface QuestionVersionPatchPayload {
    text?: string;
    difficulty?: Difficulty;
    explanation?: string;
    topic_ids?: string[];
    source_type?: QuestionSourceType | null;
    source_name?: string | null;
    source_reference?: string | null;
    source_year?: number | null;
    external_question_id?: string | null;
    choices?: Array<{ text: string; position?: number; is_correct?: boolean }>;
    true_false?: TrueFalseContent;
    assertion_reason?: {
        assertion: string;
        reason: string;
        correct_relationship: AssertionReasonRelationship;
    };
    match_following?: {
        left_items: Array<{ text: string; position?: number }>;
        right_items: Array<{ text: string; position?: number }>;
        pairs: Array<{ left_position: number; right_position: number }>;
    };
    descriptive?: DescriptiveContent;
}

export interface RowValidationError {
    row_number: number;
    field: string;
    message: string;
    raw_data?: Record<string, unknown>;
}

export interface ParsedRowPreview {
    row_number: number;
    is_valid: boolean;
    is_duplicate: boolean;
    duplicate_type?: "STRONG" | "POTENTIAL" | null;
    duplicate_reason: string | null;
    question_type: QuestionType | null;
    text: string;
    difficulty: Difficulty | null;
    topic_name?: string;
    topic_id?: string | null;
    source_type?: string | null;
    source_year?: number | null;
    external_question_id?: string | null;
    errors: string[];
}

export interface QuestionImportPreviewResponse {
    total_rows: number;
    valid_rows: number;
    invalid_rows: number;
    duplicate_rows: number;
    can_import: boolean;
    summary: Record<string, number>;
    errors: RowValidationError[];
    rows: ParsedRowPreview[];
}

export interface QuestionImportExecuteResponse {
    total_rows: number;
    imported_rows: number;
    skipped_rows: number;
    failed_rows: number;
    created_question_ids: string[];
    errors: string[];
}
