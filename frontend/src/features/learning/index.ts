// Public API for the learning feature.
export { StudentCurriculumBrowser } from "./components/StudentCurriculumBrowser";
export { AdminTaxonomyManager } from "./components/AdminTaxonomyManager";
export { LearningBreadcrumbs } from "./components/LearningBreadcrumbs";

export { learningApi } from "./api/learningApi";

export {
    learningKeys,
    useDomains,
    useDomain,
    useSubjects,
    useSubject,
    useChapters,
    useChapter,
    useTopics,
    useTopic,
    useCreateDomain,
    useUpdateDomain,
    useDeleteDomain,
    useCreateSubject,
    useUpdateSubject,
    useDeleteSubject,
    useCreateChapter,
    useUpdateChapter,
    useDeleteChapter,
    useCreateTopic,
    useUpdateTopic,
    useDeleteTopic,
} from "./hooks/useLearning";

export type {
    Domain,
    Subject,
    Chapter,
    Topic,
    PaginatedResponse,
    CurriculumListParams,
    SubjectListParams,
    ChapterListParams,
    TopicListParams,
    CreateDomainPayload,
    UpdateDomainPayload,
    CreateSubjectPayload,
    UpdateSubjectPayload,
    CreateChapterPayload,
    UpdateChapterPayload,
    CreateTopicPayload,
    UpdateTopicPayload,
} from "./types/learning.types";
