// Public API for the question-bank feature.

export { questionBankApi } from "./api/questionBankApi";

export {
    questionBankKeys,
    useQuestions,
    useQuestion,
    useQuestionVersions,
    useQuestionVersion,
    useCreateQuestion,
    useCreateQuestionVersion,
    useUpdateDraftVersion,
    useSubmitReview,
    useApproveVersion,
    usePublishVersion,
    useArchiveVersion,
} from "./hooks/useQuestionBank";

export { QuestionStatusBadge } from "./components/QuestionStatusBadge";
export { LifecycleActions } from "./components/LifecycleActions";
export { VersionHistoryList } from "./components/VersionHistoryList";
export { QuestionForm } from "./components/QuestionForm";
export { QuestionRenderer } from "./components/delivery/QuestionRenderer";
export { QuestionImportView } from "./components/QuestionImportView";
export { useQuestionImport } from "./hooks/useQuestionImport";

export { McqEditor } from "./components/editors/McqEditor";
export { MultipleSelectEditor } from "./components/editors/MultipleSelectEditor";
export { TrueFalseEditor } from "./components/editors/TrueFalseEditor";
export { AssertionReasonEditor } from "./components/editors/AssertionReasonEditor";
export { MatchFollowingEditor } from "./components/editors/MatchFollowingEditor";
export { DescriptiveEditor } from "./components/editors/DescriptiveEditor";

export type {
    AssertionReasonContent,
    AssertionReasonRelationship,
    BaseQuestionCreatePayload,
    ChoiceItem,
    DescriptiveContent,
    Difficulty,
    MatchFollowingContent,
    MatchItem,
    MatchPair,
    PaginatedResponse,
    ParsedRowPreview,
    QuestionAdminResponse,
    QuestionCreatePayload,
    QuestionFilterParams,
    QuestionImportExecuteResponse,
    QuestionImportPreviewResponse,
    QuestionSourceType,
    QuestionStatus,
    QuestionStudentResponse,
    QuestionType,
    QuestionVersionAdminResponse,
    QuestionVersionCreatePayload,
    QuestionVersionFilterParams,
    QuestionVersionPatchPayload,
    QuestionVersionStudentResponse,
    RowValidationError,
    TrueFalseContent,
} from "./types/questionBank.types";
