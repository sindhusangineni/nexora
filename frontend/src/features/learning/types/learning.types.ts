export interface Domain {
    id: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
}

export interface Subject {
    id: string;
    domain: string;
    name: string;
    description: string;
    position: number;
    created_at: string;
    updated_at: string;
}

export interface Chapter {
    id: string;
    subject: string;
    name: string;
    description: string;
    position: number;
    created_at: string;
    updated_at: string;
}

export interface Topic {
    id: string;
    chapter: string;
    name: string;
    description: string;
    position: number;
    created_at: string;
    updated_at: string;
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export interface CurriculumListParams {
    page?: number;
    page_size?: number;
    search?: string;
}

export interface SubjectListParams extends CurriculumListParams {
    domain?: string;
}

export interface ChapterListParams extends CurriculumListParams {
    subject?: string;
}

export interface TopicListParams extends CurriculumListParams {
    chapter?: string;
}

export interface CreateDomainPayload {
    name: string;
    description?: string;
}

export interface UpdateDomainPayload {
    name?: string;
    description?: string;
}

export interface CreateSubjectPayload {
    domain: string;
    name: string;
    description?: string;
    position?: number;
}

export interface UpdateSubjectPayload {
    name?: string;
    description?: string;
    position?: number;
}

export interface CreateChapterPayload {
    subject: string;
    name: string;
    description?: string;
    position?: number;
}

export interface UpdateChapterPayload {
    name?: string;
    description?: string;
    position?: number;
}

export interface CreateTopicPayload {
    chapter: string;
    name: string;
    description?: string;
    position?: number;
}

export interface UpdateTopicPayload {
    name?: string;
    description?: string;
    position?: number;
}
