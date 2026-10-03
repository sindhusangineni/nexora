import { useState } from "react";

import { Button } from "@/shared/ui/Button";
import { LoadingScreen } from "@/shared/components/LoadingScreen";
import { parseApiError } from "@/lib/api";
import {
    useChapters,
    useDomains,
    useSubjects,
    useTopics,
} from "../hooks/useLearning";
import { LearningBreadcrumbs } from "./LearningBreadcrumbs";
import type { Chapter, Domain, Subject, Topic } from "../types/learning.types";

export function StudentCurriculumBrowser() {
    // Selected hierarchy nodes
    const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
    const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
    const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null);
    const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

    // Search filters
    const [domainSearch, setDomainSearch] = useState("");
    const [subjectSearch, setSubjectSearch] = useState("");
    const [chapterSearch, setChapterSearch] = useState("");
    const [topicSearch, setTopicSearch] = useState("");

    // Queries
    const domainsQuery = useDomains(
        { search: domainSearch || undefined },
        { enabled: !selectedDomain },
    );

    const subjectsQuery = useSubjects(
        {
            domain: selectedDomain?.id,
            search: subjectSearch || undefined,
        },
        { enabled: Boolean(selectedDomain && !selectedSubject) },
    );

    const chaptersQuery = useChapters(
        {
            subject: selectedSubject?.id,
            search: chapterSearch || undefined,
        },
        { enabled: Boolean(selectedSubject && !selectedChapter) },
    );

    const topicsQuery = useTopics(
        {
            chapter: selectedChapter?.id,
            search: topicSearch || undefined,
        },
        { enabled: Boolean(selectedChapter) },
    );

    // Breadcrumb navigation handler
    const handleBreadcrumbNavigate = (
        level: "root" | "domain" | "subject" | "chapter",
    ) => {
        if (level === "root") {
            setSelectedDomain(null);
            setSelectedSubject(null);
            setSelectedChapter(null);
            setSelectedTopic(null);
            setSubjectSearch("");
            setChapterSearch("");
            setTopicSearch("");
        } else if (level === "domain") {
            setSelectedSubject(null);
            setSelectedChapter(null);
            setSelectedTopic(null);
            setChapterSearch("");
            setTopicSearch("");
        } else if (level === "subject") {
            setSelectedChapter(null);
            setSelectedTopic(null);
            setTopicSearch("");
        } else if (level === "chapter") {
            setSelectedTopic(null);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header & Breadcrumbs */}
            <div className="space-y-3 pb-2 border-b border-border">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-foreground">
                            Curriculum & Learning
                        </h1>
                        <p className="text-sm text-foreground-muted mt-0.5">
                            Browse syllabus domains, subjects, chapters, and topics.
                        </p>
                    </div>
                </div>

                <LearningBreadcrumbs
                    domain={selectedDomain}
                    subject={selectedSubject}
                    chapter={selectedChapter}
                    topic={selectedTopic}
                    onNavigate={handleBreadcrumbNavigate}
                />
            </div>

            {/* LEVEL 1: DOMAINS */}
            {!selectedDomain && (
                <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
                        <h2 className="text-lg font-semibold text-foreground">
                            Available Domains
                        </h2>
                        <div className="w-full sm:w-72">
                            <input
                                type="search"
                                value={domainSearch}
                                onChange={(e) => setDomainSearch(e.target.value)}
                                placeholder="Search domains..."
                                aria-label="Search domains"
                                className="w-full h-9 px-3 text-sm rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>

                    {domainsQuery.isLoading && (
                        <LoadingScreen message="Loading curriculum domains..." />
                    )}

                    {domainsQuery.isError && (
                        <div
                            role="alert"
                            className="p-6 text-center rounded-lg border border-danger/20 bg-red-50 text-danger space-y-3"
                        >
                            <p className="font-medium text-sm">
                                {parseApiError(domainsQuery.error).message}
                            </p>
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => domainsQuery.refetch()}
                            >
                                Retry
                            </Button>
                        </div>
                    )}

                    {domainsQuery.isSuccess && (
                        <>
                            {domainsQuery.data.results.length === 0 ? (
                                <div className="p-12 text-center rounded-lg border border-dashed border-border bg-surface-muted">
                                    <p className="text-sm font-medium text-foreground-muted">
                                        {domainSearch
                                            ? "No domains match your search query."
                                            : "No curriculum domains are currently available."}
                                    </p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {domainsQuery.data.results.map((domain) => (
                                        <div
                                            key={domain.id}
                                            className="flex flex-col justify-between p-6 rounded-xl border border-border bg-surface shadow-xs hover:border-primary-400 hover:shadow-sm transition-all cursor-pointer group"
                                            onClick={() => setSelectedDomain(domain)}
                                        >
                                            <div className="space-y-2">
                                                <h3 className="text-base font-semibold text-foreground group-hover:text-primary-600 transition-colors">
                                                    {domain.name}
                                                </h3>
                                                <p className="text-sm text-foreground-muted line-clamp-3">
                                                    {domain.description || "No description provided."}
                                                </p>
                                            </div>
                                            <div className="pt-4 flex items-center justify-between text-xs text-primary-600 font-medium">
                                                <span>Explore Curriculum</span>
                                                <span aria-hidden="true">&rarr;</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* LEVEL 2: SUBJECTS (Domain Selected) */}
            {selectedDomain && !selectedSubject && (
                <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-lg font-semibold text-foreground">
                                Subjects in {selectedDomain.name}
                            </h2>
                            {selectedDomain.description && (
                                <p className="text-xs text-foreground-muted mt-0.5">
                                    {selectedDomain.description}
                                </p>
                            )}
                        </div>
                        <div className="w-full sm:w-72">
                            <input
                                type="search"
                                value={subjectSearch}
                                onChange={(e) => setSubjectSearch(e.target.value)}
                                placeholder="Search subjects..."
                                aria-label="Search subjects"
                                className="w-full h-9 px-3 text-sm rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>

                    {subjectsQuery.isLoading && (
                        <LoadingScreen message="Loading subjects..." />
                    )}

                    {subjectsQuery.isError && (
                        <div
                            role="alert"
                            className="p-6 text-center rounded-lg border border-danger/20 bg-red-50 text-danger space-y-3"
                        >
                            <p className="font-medium text-sm">
                                {parseApiError(subjectsQuery.error).message}
                            </p>
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => subjectsQuery.refetch()}
                            >
                                Retry
                            </Button>
                        </div>
                    )}

                    {subjectsQuery.isSuccess && (
                        <>
                            {subjectsQuery.data.results.length === 0 ? (
                                <div className="p-12 text-center rounded-lg border border-dashed border-border bg-surface-muted">
                                    <p className="text-sm font-medium text-foreground-muted">
                                        {subjectSearch
                                            ? "No subjects match your search query."
                                            : "No subjects found in this domain yet."}
                                    </p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {subjectsQuery.data.results.map((subject) => (
                                        <div
                                            key={subject.id}
                                            className="flex flex-col justify-between p-6 rounded-xl border border-border bg-surface shadow-xs hover:border-primary-400 hover:shadow-sm transition-all cursor-pointer group"
                                            onClick={() => setSelectedSubject(subject)}
                                        >
                                            <div className="space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <h3 className="text-base font-semibold text-foreground group-hover:text-primary-600 transition-colors">
                                                        {subject.name}
                                                    </h3>
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-600 font-mono">
                                                        #{subject.position}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-foreground-muted line-clamp-3">
                                                    {subject.description || "No description provided."}
                                                </p>
                                            </div>
                                            <div className="pt-4 flex items-center justify-between text-xs text-primary-600 font-medium">
                                                <span>View Chapters</span>
                                                <span aria-hidden="true">&rarr;</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* LEVEL 3: CHAPTERS (Subject Selected) */}
            {selectedSubject && !selectedChapter && (
                <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-lg font-semibold text-foreground">
                                Chapters in {selectedSubject.name}
                            </h2>
                            {selectedSubject.description && (
                                <p className="text-xs text-foreground-muted mt-0.5">
                                    {selectedSubject.description}
                                </p>
                            )}
                        </div>
                        <div className="w-full sm:w-72">
                            <input
                                type="search"
                                value={chapterSearch}
                                onChange={(e) => setChapterSearch(e.target.value)}
                                placeholder="Search chapters..."
                                aria-label="Search chapters"
                                className="w-full h-9 px-3 text-sm rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>

                    {chaptersQuery.isLoading && (
                        <LoadingScreen message="Loading chapters..." />
                    )}

                    {chaptersQuery.isError && (
                        <div
                            role="alert"
                            className="p-6 text-center rounded-lg border border-danger/20 bg-red-50 text-danger space-y-3"
                        >
                            <p className="font-medium text-sm">
                                {parseApiError(chaptersQuery.error).message}
                            </p>
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => chaptersQuery.refetch()}
                            >
                                Retry
                            </Button>
                        </div>
                    )}

                    {chaptersQuery.isSuccess && (
                        <>
                            {chaptersQuery.data.results.length === 0 ? (
                                <div className="p-12 text-center rounded-lg border border-dashed border-border bg-surface-muted">
                                    <p className="text-sm font-medium text-foreground-muted">
                                        {chapterSearch
                                            ? "No chapters match your search query."
                                            : "No chapters found in this subject yet."}
                                    </p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {chaptersQuery.data.results.map((chapter) => (
                                        <div
                                            key={chapter.id}
                                            className="flex flex-col justify-between p-6 rounded-xl border border-border bg-surface shadow-xs hover:border-primary-400 hover:shadow-sm transition-all cursor-pointer group"
                                            onClick={() => setSelectedChapter(chapter)}
                                        >
                                            <div className="space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <h3 className="text-base font-semibold text-foreground group-hover:text-primary-600 transition-colors">
                                                        {chapter.name}
                                                    </h3>
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-600 font-mono">
                                                        #{chapter.position}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-foreground-muted line-clamp-3">
                                                    {chapter.description || "No description provided."}
                                                </p>
                                            </div>
                                            <div className="pt-4 flex items-center justify-between text-xs text-primary-600 font-medium">
                                                <span>View Topics</span>
                                                <span aria-hidden="true">&rarr;</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* LEVEL 4: TOPICS (Chapter Selected) */}
            {selectedChapter && (
                <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-lg font-semibold text-foreground">
                                Topics in {selectedChapter.name}
                            </h2>
                            {selectedChapter.description && (
                                <p className="text-xs text-foreground-muted mt-0.5">
                                    {selectedChapter.description}
                                </p>
                            )}
                        </div>
                        <div className="w-full sm:w-72">
                            <input
                                type="search"
                                value={topicSearch}
                                onChange={(e) => setTopicSearch(e.target.value)}
                                placeholder="Search topics..."
                                aria-label="Search topics"
                                className="w-full h-9 px-3 text-sm rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>

                    {topicsQuery.isLoading && (
                        <LoadingScreen message="Loading topics..." />
                    )}

                    {topicsQuery.isError && (
                        <div
                            role="alert"
                            className="p-6 text-center rounded-lg border border-danger/20 bg-red-50 text-danger space-y-3"
                        >
                            <p className="font-medium text-sm">
                                {parseApiError(topicsQuery.error).message}
                            </p>
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => topicsQuery.refetch()}
                            >
                                Retry
                            </Button>
                        </div>
                    )}

                    {topicsQuery.isSuccess && (
                        <>
                            {topicsQuery.data.results.length === 0 ? (
                                <div className="p-12 text-center rounded-lg border border-dashed border-border bg-surface-muted">
                                    <p className="text-sm font-medium text-foreground-muted">
                                        {topicSearch
                                            ? "No topics match your search query."
                                            : "No topics found in this chapter yet."}
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {topicsQuery.data.results.map((topic) => (
                                        <div
                                            key={topic.id}
                                            className="p-5 rounded-lg border border-border bg-surface shadow-xs space-y-2"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="space-y-1">
                                                    <div className="flex items-center space-x-2">
                                                        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary-50 text-primary-700 border border-primary-200 font-mono">
                                                            Topic #{topic.position}
                                                        </span>
                                                        <h3 className="text-base font-semibold text-foreground">
                                                            {topic.name}
                                                        </h3>
                                                    </div>
                                                    <p className="text-sm text-foreground-muted whitespace-pre-line">
                                                        {topic.description || "No topic syllabus description provided."}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
