import { useState } from "react";

import { Button } from "@/shared/ui/Button";
import { parseApiError } from "@/lib/api";
import {
    useChapters,
    useCreateChapter,
    useCreateDomain,
    useCreateSubject,
    useCreateTopic,
    useDeleteChapter,
    useDeleteDomain,
    useDeleteSubject,
    useDeleteTopic,
    useDomains,
    useSubjects,
    useTopics,
    useUpdateChapter,
    useUpdateDomain,
    useUpdateSubject,
    useUpdateTopic,
} from "../hooks/useLearning";
import { LearningBreadcrumbs } from "./LearningBreadcrumbs";
import { DomainFormModal } from "./DomainFormModal";
import { SubjectFormModal } from "./SubjectFormModal";
import { ChapterFormModal } from "./ChapterFormModal";
import { TopicFormModal } from "./TopicFormModal";
import { DeleteConfirmModal } from "./DeleteConfirmModal";
import type { Chapter, Domain, Subject, Topic } from "../types/learning.types";

export function AdminTaxonomyManager() {
    // Selected entities
    const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
    const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
    const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null);

    // Search filters
    const [domainSearch, setDomainSearch] = useState("");
    const [subjectSearch, setSubjectSearch] = useState("");
    const [chapterSearch, setChapterSearch] = useState("");
    const [topicSearch, setTopicSearch] = useState("");

    // Modal state
    const [domainModalOpen, setDomainModalOpen] = useState(false);
    const [editingDomain, setEditingDomain] = useState<Domain | null>(null);

    const [subjectModalOpen, setSubjectModalOpen] = useState(false);
    const [editingSubject, setEditingSubject] = useState<Subject | null>(null);

    const [chapterModalOpen, setChapterModalOpen] = useState(false);
    const [editingChapter, setEditingChapter] = useState<Chapter | null>(null);

    const [topicModalOpen, setTopicModalOpen] = useState(false);
    const [editingTopic, setEditingTopic] = useState<Topic | null>(null);

    // Delete modal state
    const [deleteModal, setDeleteModal] = useState<{
        isOpen: boolean;
        type: "Domain" | "Subject" | "Chapter" | "Topic";
        id: string;
        name: string;
        errorMessage: string | null;
    }>({
        isOpen: false,
        type: "Domain",
        id: "",
        name: "",
        errorMessage: null,
    });

    // Queries
    const domainsQuery = useDomains({ search: domainSearch || undefined });
    const subjectsQuery = useSubjects(
        { domain: selectedDomain?.id, search: subjectSearch || undefined },
        { enabled: Boolean(selectedDomain) },
    );
    const chaptersQuery = useChapters(
        { subject: selectedSubject?.id, search: chapterSearch || undefined },
        { enabled: Boolean(selectedSubject) },
    );
    const topicsQuery = useTopics(
        { chapter: selectedChapter?.id, search: topicSearch || undefined },
        { enabled: Boolean(selectedChapter) },
    );

    // Mutations
    const createDomainMutation = useCreateDomain();
    const updateDomainMutation = useUpdateDomain();
    const deleteDomainMutation = useDeleteDomain();

    const createSubjectMutation = useCreateSubject();
    const updateSubjectMutation = useUpdateSubject();
    const deleteSubjectMutation = useDeleteSubject();

    const createChapterMutation = useCreateChapter();
    const updateChapterMutation = useUpdateChapter();
    const deleteChapterMutation = useDeleteChapter();

    const createTopicMutation = useCreateTopic();
    const updateTopicMutation = useUpdateTopic();
    const deleteTopicMutation = useDeleteTopic();

    // Handlers
    const handleBreadcrumbNavigate = (
        level: "root" | "domain" | "subject" | "chapter",
    ) => {
        if (level === "root") {
            setSelectedDomain(null);
            setSelectedSubject(null);
            setSelectedChapter(null);
        } else if (level === "domain") {
            setSelectedSubject(null);
            setSelectedChapter(null);
        } else if (level === "subject") {
            setSelectedChapter(null);
        }
    };

    const handleDeleteConfirm = async () => {
        try {
            if (deleteModal.type === "Domain") {
                await deleteDomainMutation.mutateAsync(deleteModal.id);
                if (selectedDomain?.id === deleteModal.id) {
                    setSelectedDomain(null);
                    setSelectedSubject(null);
                    setSelectedChapter(null);
                }
            } else if (deleteModal.type === "Subject") {
                await deleteSubjectMutation.mutateAsync(deleteModal.id);
                if (selectedSubject?.id === deleteModal.id) {
                    setSelectedSubject(null);
                    setSelectedChapter(null);
                }
            } else if (deleteModal.type === "Chapter") {
                await deleteChapterMutation.mutateAsync(deleteModal.id);
                if (selectedChapter?.id === deleteModal.id) {
                    setSelectedChapter(null);
                }
            } else if (deleteModal.type === "Topic") {
                await deleteTopicMutation.mutateAsync(deleteModal.id);
            }
            setDeleteModal((prev) => ({ ...prev, isOpen: false, errorMessage: null }));
        } catch (err) {
            const parsed = parseApiError(err);
            setDeleteModal((prev) => ({
                ...prev,
                errorMessage: parsed.message,
            }));
            throw err;
        }
    };

    return (
        <div className="space-y-6">
            {/* Header & Breadcrumb */}
            <div className="space-y-3 pb-2 border-b border-border">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-foreground">
                            Learning Taxonomy Management
                        </h1>
                        <p className="text-sm text-foreground-muted mt-0.5">
                            Author and organize curriculum domains, subjects, chapters, and topics.
                        </p>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                                setEditingDomain(null);
                                setDomainModalOpen(true);
                            }}
                        >
                            + New Domain
                        </Button>
                    </div>
                </div>

                <LearningBreadcrumbs
                    domain={selectedDomain}
                    subject={selectedSubject}
                    chapter={selectedChapter}
                    onNavigate={handleBreadcrumbNavigate}
                />
            </div>

            {/* Hierarchical Columns / Explorer */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-start">
                {/* COLUMN 1: DOMAINS */}
                <div className="p-4 rounded-xl border border-border bg-surface shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-bold text-foreground uppercase tracking-wider">
                            Domains
                        </h2>
                        <span className="text-xs text-foreground-muted font-mono">
                            {domainsQuery.data?.count ?? 0}
                        </span>
                    </div>

                    <input
                        type="search"
                        value={domainSearch}
                        onChange={(e) => setDomainSearch(e.target.value)}
                        placeholder="Search domains..."
                        aria-label="Filter domains"
                        className="w-full h-8 px-2.5 text-xs rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-1 focus:ring-primary-500"
                    />

                    {domainsQuery.isLoading && (
                        <div className="py-8 text-center text-xs text-foreground-muted">
                            Loading domains...
                        </div>
                    )}

                    {domainsQuery.isError && (
                        <div className="p-3 text-xs rounded-md bg-red-50 text-danger">
                            {parseApiError(domainsQuery.error).message}
                        </div>
                    )}

                    {domainsQuery.isSuccess && (
                        <div className="space-y-1.5 max-h-[600px] overflow-y-auto">
                            {domainsQuery.data.results.length === 0 ? (
                                <p className="text-xs text-foreground-muted text-center py-6">
                                    No domains found.
                                </p>
                            ) : (
                                domainsQuery.data.results.map((domain) => {
                                    const isSelected = selectedDomain?.id === domain.id;
                                    return (
                                        <div
                                            key={domain.id}
                                            className={`p-3 rounded-lg border transition-all text-sm cursor-pointer group ${
                                                isSelected
                                                    ? "bg-primary-50 border-primary-300 text-primary-900"
                                                    : "bg-surface border-border hover:border-neutral-300 text-foreground"
                                            }`}
                                            onClick={() => {
                                                setSelectedDomain(domain);
                                                setSelectedSubject(null);
                                                setSelectedChapter(null);
                                            }}
                                        >
                                            <div className="flex items-center justify-between gap-1">
                                                <span className="font-semibold truncate">
                                                    {domain.name}
                                                </span>
                                                <div
                                                    className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    <button
                                                        type="button"
                                                        title="Edit Domain"
                                                        aria-label={`Edit Domain ${domain.name}`}
                                                        onClick={() => {
                                                            setEditingDomain(domain);
                                                            setDomainModalOpen(true);
                                                        }}
                                                        className="text-xs p-1 text-foreground-muted hover:text-foreground rounded"
                                                    >
                                                        &#9998;
                                                    </button>
                                                    <button
                                                        type="button"
                                                        title="Delete Domain"
                                                        aria-label={`Delete Domain ${domain.name}`}
                                                        onClick={() => {
                                                            setDeleteModal({
                                                                isOpen: true,
                                                                type: "Domain",
                                                                id: domain.id,
                                                                name: domain.name,
                                                                errorMessage: null,
                                                            });
                                                        }}
                                                        className="text-xs p-1 text-danger hover:bg-red-50 rounded"
                                                    >
                                                        &#128465;
                                                    </button>
                                                </div>
                                            </div>
                                            {domain.description && (
                                                <p className="text-xs text-foreground-muted line-clamp-1 mt-1">
                                                    {domain.description}
                                                </p>
                                            )}
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    )}
                </div>

                {/* COLUMN 2: SUBJECTS */}
                <div className="p-4 rounded-xl border border-border bg-surface shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-bold text-foreground uppercase tracking-wider">
                            Subjects
                        </h2>
                        {selectedDomain && (
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                    setEditingSubject(null);
                                    setSubjectModalOpen(true);
                                }}
                            >
                                + Add
                            </Button>
                        )}
                    </div>

                    {!selectedDomain ? (
                        <div className="py-12 text-center text-xs text-foreground-muted border border-dashed border-border rounded-lg">
                            Select a domain to view its subjects.
                        </div>
                    ) : (
                        <>
                            <input
                                type="search"
                                value={subjectSearch}
                                onChange={(e) => setSubjectSearch(e.target.value)}
                                placeholder="Search subjects..."
                                aria-label="Filter subjects"
                                className="w-full h-8 px-2.5 text-xs rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />

                            {subjectsQuery.isLoading && (
                                <div className="py-8 text-center text-xs text-foreground-muted">
                                    Loading subjects...
                                </div>
                            )}

                            {subjectsQuery.isError && (
                                <div className="p-3 text-xs rounded-md bg-red-50 text-danger">
                                    {parseApiError(subjectsQuery.error).message}
                                </div>
                            )}

                            {subjectsQuery.isSuccess && (
                                <div className="space-y-1.5 max-h-[600px] overflow-y-auto">
                                    {subjectsQuery.data.results.length === 0 ? (
                                        <p className="text-xs text-foreground-muted text-center py-6">
                                            No subjects found in this domain.
                                        </p>
                                    ) : (
                                        subjectsQuery.data.results.map((subject) => {
                                            const isSelected = selectedSubject?.id === subject.id;
                                            return (
                                                <div
                                                    key={subject.id}
                                                    className={`p-3 rounded-lg border transition-all text-sm cursor-pointer group ${
                                                        isSelected
                                                            ? "bg-primary-50 border-primary-300 text-primary-900"
                                                            : "bg-surface border-border hover:border-neutral-300 text-foreground"
                                                    }`}
                                                    onClick={() => {
                                                        setSelectedSubject(subject);
                                                        setSelectedChapter(null);
                                                    }}
                                                >
                                                    <div className="flex items-center justify-between gap-1">
                                                        <div className="flex items-center space-x-1.5 truncate">
                                                            <span className="text-[10px] font-mono px-1 rounded bg-neutral-100 text-neutral-600">
                                                                #{subject.position}
                                                            </span>
                                                            <span className="font-semibold truncate">
                                                                {subject.name}
                                                            </span>
                                                        </div>
                                                        <div
                                                            className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1"
                                                            onClick={(e) => e.stopPropagation()}
                                                        >
                                                            <button
                                                                type="button"
                                                                title="Edit Subject"
                                                                aria-label={`Edit Subject ${subject.name}`}
                                                                onClick={() => {
                                                                    setEditingSubject(subject);
                                                                    setSubjectModalOpen(true);
                                                                }}
                                                                className="text-xs p-1 text-foreground-muted hover:text-foreground rounded"
                                                            >
                                                                &#9998;
                                                            </button>
                                                            <button
                                                                type="button"
                                                                title="Delete Subject"
                                                                aria-label={`Delete Subject ${subject.name}`}
                                                                onClick={() => {
                                                                    setDeleteModal({
                                                                        isOpen: true,
                                                                        type: "Subject",
                                                                        id: subject.id,
                                                                        name: subject.name,
                                                                        errorMessage: null,
                                                                    });
                                                                }}
                                                                className="text-xs p-1 text-danger hover:bg-red-50 rounded"
                                                            >
                                                                &#128465;
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* COLUMN 3: CHAPTERS */}
                <div className="p-4 rounded-xl border border-border bg-surface shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-bold text-foreground uppercase tracking-wider">
                            Chapters
                        </h2>
                        {selectedSubject && (
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                    setEditingChapter(null);
                                    setChapterModalOpen(true);
                                }}
                            >
                                + Add
                            </Button>
                        )}
                    </div>

                    {!selectedSubject ? (
                        <div className="py-12 text-center text-xs text-foreground-muted border border-dashed border-border rounded-lg">
                            Select a subject to view its chapters.
                        </div>
                    ) : (
                        <>
                            <input
                                type="search"
                                value={chapterSearch}
                                onChange={(e) => setChapterSearch(e.target.value)}
                                placeholder="Search chapters..."
                                aria-label="Filter chapters"
                                className="w-full h-8 px-2.5 text-xs rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />

                            {chaptersQuery.isLoading && (
                                <div className="py-8 text-center text-xs text-foreground-muted">
                                    Loading chapters...
                                </div>
                            )}

                            {chaptersQuery.isError && (
                                <div className="p-3 text-xs rounded-md bg-red-50 text-danger">
                                    {parseApiError(chaptersQuery.error).message}
                                </div>
                            )}

                            {chaptersQuery.isSuccess && (
                                <div className="space-y-1.5 max-h-[600px] overflow-y-auto">
                                    {chaptersQuery.data.results.length === 0 ? (
                                        <p className="text-xs text-foreground-muted text-center py-6">
                                            No chapters found in this subject.
                                        </p>
                                    ) : (
                                        chaptersQuery.data.results.map((chapter) => {
                                            const isSelected = selectedChapter?.id === chapter.id;
                                            return (
                                                <div
                                                    key={chapter.id}
                                                    className={`p-3 rounded-lg border transition-all text-sm cursor-pointer group ${
                                                        isSelected
                                                            ? "bg-primary-50 border-primary-300 text-primary-900"
                                                            : "bg-surface border-border hover:border-neutral-300 text-foreground"
                                                    }`}
                                                    onClick={() => setSelectedChapter(chapter)}
                                                >
                                                    <div className="flex items-center justify-between gap-1">
                                                        <div className="flex items-center space-x-1.5 truncate">
                                                            <span className="text-[10px] font-mono px-1 rounded bg-neutral-100 text-neutral-600">
                                                                #{chapter.position}
                                                            </span>
                                                            <span className="font-semibold truncate">
                                                                {chapter.name}
                                                            </span>
                                                        </div>
                                                        <div
                                                            className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1"
                                                            onClick={(e) => e.stopPropagation()}
                                                        >
                                                            <button
                                                                type="button"
                                                                title="Edit Chapter"
                                                                aria-label={`Edit Chapter ${chapter.name}`}
                                                                onClick={() => {
                                                                    setEditingChapter(chapter);
                                                                    setChapterModalOpen(true);
                                                                }}
                                                                className="text-xs p-1 text-foreground-muted hover:text-foreground rounded"
                                                            >
                                                                &#9998;
                                                            </button>
                                                            <button
                                                                type="button"
                                                                title="Delete Chapter"
                                                                aria-label={`Delete Chapter ${chapter.name}`}
                                                                onClick={() => {
                                                                    setDeleteModal({
                                                                        isOpen: true,
                                                                        type: "Chapter",
                                                                        id: chapter.id,
                                                                        name: chapter.name,
                                                                        errorMessage: null,
                                                                    });
                                                                }}
                                                                className="text-xs p-1 text-danger hover:bg-red-50 rounded"
                                                            >
                                                                &#128465;
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* COLUMN 4: TOPICS */}
                <div className="p-4 rounded-xl border border-border bg-surface shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-bold text-foreground uppercase tracking-wider">
                            Topics
                        </h2>
                        {selectedChapter && (
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                    setEditingTopic(null);
                                    setTopicModalOpen(true);
                                }}
                            >
                                + Add
                            </Button>
                        )}
                    </div>

                    {!selectedChapter ? (
                        <div className="py-12 text-center text-xs text-foreground-muted border border-dashed border-border rounded-lg">
                            Select a chapter to view its topics.
                        </div>
                    ) : (
                        <>
                            <input
                                type="search"
                                value={topicSearch}
                                onChange={(e) => setTopicSearch(e.target.value)}
                                placeholder="Search topics..."
                                aria-label="Filter topics"
                                className="w-full h-8 px-2.5 text-xs rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />

                            {topicsQuery.isLoading && (
                                <div className="py-8 text-center text-xs text-foreground-muted">
                                    Loading topics...
                                </div>
                            )}

                            {topicsQuery.isError && (
                                <div className="p-3 text-xs rounded-md bg-red-50 text-danger">
                                    {parseApiError(topicsQuery.error).message}
                                </div>
                            )}

                            {topicsQuery.isSuccess && (
                                <div className="space-y-1.5 max-h-[600px] overflow-y-auto">
                                    {topicsQuery.data.results.length === 0 ? (
                                        <p className="text-xs text-foreground-muted text-center py-6">
                                            No topics found in this chapter.
                                        </p>
                                    ) : (
                                        topicsQuery.data.results.map((topic) => (
                                            <div
                                                key={topic.id}
                                                className="p-3 rounded-lg border border-border bg-surface text-foreground shadow-2xs space-y-1 group"
                                            >
                                                <div className="flex items-center justify-between gap-1">
                                                    <div className="flex items-center space-x-1.5 truncate">
                                                        <span className="text-[10px] font-mono px-1 rounded bg-neutral-100 text-neutral-600">
                                                            #{topic.position}
                                                        </span>
                                                        <span className="font-semibold truncate text-sm">
                                                            {topic.name}
                                                        </span>
                                                    </div>
                                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1">
                                                        <button
                                                            type="button"
                                                            title="Edit Topic"
                                                            aria-label={`Edit Topic ${topic.name}`}
                                                            onClick={() => {
                                                                setEditingTopic(topic);
                                                                setTopicModalOpen(true);
                                                            }}
                                                            className="text-xs p-1 text-foreground-muted hover:text-foreground rounded"
                                                        >
                                                            &#9998;
                                                        </button>
                                                        <button
                                                            type="button"
                                                            title="Delete Topic"
                                                            aria-label={`Delete Topic ${topic.name}`}
                                                            onClick={() => {
                                                                setDeleteModal({
                                                                    isOpen: true,
                                                                    type: "Topic",
                                                                    id: topic.id,
                                                                    name: topic.name,
                                                                    errorMessage: null,
                                                                });
                                                            }}
                                                            className="text-xs p-1 text-danger hover:bg-red-50 rounded"
                                                        >
                                                            &#128465;
                                                        </button>
                                                    </div>
                                                </div>
                                                {topic.description && (
                                                    <p className="text-xs text-foreground-muted line-clamp-2">
                                                        {topic.description}
                                                    </p>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* DOMAIN FORM MODAL */}
            <DomainFormModal
                isOpen={domainModalOpen}
                onClose={() => setDomainModalOpen(false)}
                initialData={editingDomain}
                onSubmit={async (payload) => {
                    if (editingDomain) {
                        await updateDomainMutation.mutateAsync({
                            id: editingDomain.id,
                            payload,
                        });
                        if (selectedDomain?.id === editingDomain.id) {
                            setSelectedDomain((prev) => (prev ? { ...prev, ...payload } : null));
                        }
                    } else {
                        await createDomainMutation.mutateAsync(payload);
                    }
                }}
            />

            {/* SUBJECT FORM MODAL */}
            {selectedDomain && (
                <SubjectFormModal
                    isOpen={subjectModalOpen}
                    onClose={() => setSubjectModalOpen(false)}
                    domainId={selectedDomain.id}
                    domainName={selectedDomain.name}
                    initialData={editingSubject}
                    onSubmit={async (payload) => {
                        if (editingSubject) {
                            await updateSubjectMutation.mutateAsync({
                                id: editingSubject.id,
                                payload,
                            });
                            if (selectedSubject?.id === editingSubject.id) {
                                setSelectedSubject((prev) =>
                                    prev ? { ...prev, ...payload } : null,
                                );
                            }
                        } else {
                            await createSubjectMutation.mutateAsync(payload);
                        }
                    }}
                />
            )}

            {/* CHAPTER FORM MODAL */}
            {selectedSubject && (
                <ChapterFormModal
                    isOpen={chapterModalOpen}
                    onClose={() => setChapterModalOpen(false)}
                    subjectId={selectedSubject.id}
                    subjectName={selectedSubject.name}
                    initialData={editingChapter}
                    onSubmit={async (payload) => {
                        if (editingChapter) {
                            await updateChapterMutation.mutateAsync({
                                id: editingChapter.id,
                                payload,
                            });
                            if (selectedChapter?.id === editingChapter.id) {
                                setSelectedChapter((prev) =>
                                    prev ? { ...prev, ...payload } : null,
                                );
                            }
                        } else {
                            await createChapterMutation.mutateAsync(payload);
                        }
                    }}
                />
            )}

            {/* TOPIC FORM MODAL */}
            {selectedChapter && (
                <TopicFormModal
                    isOpen={topicModalOpen}
                    onClose={() => setTopicModalOpen(false)}
                    chapterId={selectedChapter.id}
                    chapterName={selectedChapter.name}
                    initialData={editingTopic}
                    onSubmit={async (payload) => {
                        if (editingTopic) {
                            await updateTopicMutation.mutateAsync({
                                id: editingTopic.id,
                                payload,
                            });
                        } else {
                            await createTopicMutation.mutateAsync(payload);
                        }
                    }}
                />
            )}

            {/* DELETE CONFIRM MODAL */}
            <DeleteConfirmModal
                isOpen={deleteModal.isOpen}
                onClose={() =>
                    setDeleteModal((prev) => ({ ...prev, isOpen: false, errorMessage: null }))
                }
                onConfirm={handleDeleteConfirm}
                resourceName={deleteModal.name}
                resourceType={deleteModal.type}
                errorMessage={deleteModal.errorMessage}
            />
        </div>
    );
}
