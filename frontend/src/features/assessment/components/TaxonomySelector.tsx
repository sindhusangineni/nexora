import React, { useState } from "react";
import { useDomains, useSubjects, useChapters, useTopics } from "@/features/learning";
import type { ScopeType } from "../types/assessment.types";

interface TaxonomySelectorProps {
    scopeType: ScopeType;
    scopeId: string;
    onChange: (scopeType: ScopeType, scopeId: string, label: string) => void;
    disabled?: boolean;
}

export const TaxonomySelector: React.FC<TaxonomySelectorProps> = ({
    scopeType,
    scopeId,
    onChange,
    disabled = false,
}) => {
    const [selectedDomainId, setSelectedDomainId] = useState<string>(
        scopeType === "DOMAIN" ? scopeId : "",
    );
    const [selectedSubjectId, setSelectedSubjectId] = useState<string>(
        scopeType === "SUBJECT" ? scopeId : "",
    );
    const [selectedChapterId, setSelectedChapterId] = useState<string>(
        scopeType === "CHAPTER" ? scopeId : "",
    );
    const [selectedTopicId, setSelectedTopicId] = useState<string>(
        scopeType === "TOPIC" ? scopeId : "",
    );

    const { data: domainsData, isLoading: isLoadingDomains } = useDomains();
    const domains = domainsData?.results || [];

    const { data: subjectsData, isLoading: isLoadingSubjects } = useSubjects(
        selectedDomainId ? { domain: selectedDomainId } : undefined,
        { enabled: Boolean(selectedDomainId) },
    );
    const subjects = subjectsData?.results || [];

    const { data: chaptersData, isLoading: isLoadingChapters } = useChapters(
        selectedSubjectId ? { subject: selectedSubjectId } : undefined,
        { enabled: Boolean(selectedSubjectId) },
    );
    const chapters = chaptersData?.results || [];

    const { data: topicsData, isLoading: isLoadingTopics } = useTopics(
        selectedChapterId ? { chapter: selectedChapterId } : undefined,
        { enabled: Boolean(selectedChapterId) },
    );
    const topics = topicsData?.results || [];

    const handleScopeTypeChange = (newScopeType: ScopeType) => {
        setSelectedSubjectId("");
        setSelectedChapterId("");
        setSelectedTopicId("");

        if (newScopeType === "DOMAIN" && selectedDomainId) {
            const domain = domains.find((d) => d.id === selectedDomainId);
            onChange("DOMAIN", selectedDomainId, domain ? `Domain: ${domain.name}` : "");
        } else {
            onChange(newScopeType, "", "");
        }
    };

    const handleDomainChange = (domainId: string) => {
        setSelectedDomainId(domainId);
        setSelectedSubjectId("");
        setSelectedChapterId("");
        setSelectedTopicId("");

        if (scopeType === "DOMAIN") {
            const domain = domains.find((d) => d.id === domainId);
            onChange("DOMAIN", domainId, domain ? `Domain: ${domain.name}` : "");
        } else {
            onChange(scopeType, "", "");
        }
    };

    const handleSubjectChange = (subjectId: string) => {
        setSelectedSubjectId(subjectId);
        setSelectedChapterId("");
        setSelectedTopicId("");

        if (scopeType === "SUBJECT") {
            const subject = subjects.find((s) => s.id === subjectId);
            onChange("SUBJECT", subjectId, subject ? `Subject: ${subject.name}` : "");
        } else {
            onChange(scopeType, "", "");
        }
    };

    const handleChapterChange = (chapterId: string) => {
        setSelectedChapterId(chapterId);
        setSelectedTopicId("");

        if (scopeType === "CHAPTER") {
            const chapter = chapters.find((c) => c.id === chapterId);
            onChange("CHAPTER", chapterId, chapter ? `Chapter: ${chapter.name}` : "");
        } else {
            onChange(scopeType, "", "");
        }
    };

    const handleTopicChange = (topicId: string) => {
        setSelectedTopicId(topicId);

        if (scopeType === "TOPIC") {
            const topic = topics.find((t) => t.id === topicId);
            onChange("TOPIC", topicId, topic ? `Topic: ${topic.name}` : "");
        }
    };



    return (
        <div className="space-y-4">
            <div>
                <label
                    htmlFor="scope-type-select"
                    className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                >
                    Taxonomy Scope Level
                </label>
                <select
                    id="scope-type-select"
                    value={scopeType}
                    disabled={disabled}
                    onChange={(e) => handleScopeTypeChange(e.target.value as ScopeType)}
                    className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
                >
                    <option value="TOPIC">Topic (Granular)</option>
                    <option value="CHAPTER">Chapter</option>
                    <option value="SUBJECT">Subject</option>
                    <option value="DOMAIN">Domain (Broadest)</option>
                </select>
                <p className="text-xs text-foreground-muted mt-1">
                    Select the breadth of question candidates eligible for this rule.
                </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Domain Selector */}
                <div>
                    <label
                        htmlFor="domain-select"
                        className="block text-xs font-medium text-neutral-600 mb-1"
                    >
                        Domain <span className="text-danger">*</span>
                    </label>
                    <select
                        id="domain-select"
                        value={selectedDomainId}
                        disabled={disabled || isLoadingDomains}
                        onChange={(e) => handleDomainChange(e.target.value)}
                        className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
                    >
                        <option value="">Select Domain...</option>
                        {domains.map((d) => (
                            <option key={d.id} value={d.id}>
                                {d.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Subject Selector (shown if scope is SUBJECT, CHAPTER, or TOPIC) */}
                {scopeType !== "DOMAIN" && (
                    <div>
                        <label
                            htmlFor="subject-select"
                            className="block text-xs font-medium text-neutral-600 mb-1"
                        >
                            Subject <span className="text-danger">*</span>
                        </label>
                        <select
                            id="subject-select"
                            value={selectedSubjectId}
                            disabled={disabled || !selectedDomainId || isLoadingSubjects}
                            onChange={(e) => handleSubjectChange(e.target.value)}
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
                        >
                            <option value="">Select Subject...</option>
                            {subjects.map((s) => (
                                <option key={s.id} value={s.id}>
                                    {s.name}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Chapter Selector (shown if scope is CHAPTER or TOPIC) */}
                {(scopeType === "CHAPTER" || scopeType === "TOPIC") && (
                    <div>
                        <label
                            htmlFor="chapter-select"
                            className="block text-xs font-medium text-neutral-600 mb-1"
                        >
                            Chapter <span className="text-danger">*</span>
                        </label>
                        <select
                            id="chapter-select"
                            value={selectedChapterId}
                            disabled={disabled || !selectedSubjectId || isLoadingChapters}
                            onChange={(e) => handleChapterChange(e.target.value)}
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
                        >
                            <option value="">Select Chapter...</option>
                            {chapters.map((c) => (
                                <option key={c.id} value={c.id}>
                                    {c.name}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Topic Selector (shown if scope is TOPIC) */}
                {scopeType === "TOPIC" && (
                    <div>
                        <label
                            htmlFor="topic-select"
                            className="block text-xs font-medium text-neutral-600 mb-1"
                        >
                            Topic <span className="text-danger">*</span>
                        </label>
                        <select
                            id="topic-select"
                            value={selectedTopicId}
                            disabled={disabled || !selectedChapterId || isLoadingTopics}
                            onChange={(e) => handleTopicChange(e.target.value)}
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
                        >
                            <option value="">Select Topic...</option>
                            {topics.map((t) => (
                                <option key={t.id} value={t.id}>
                                    {t.name}
                                </option>
                            ))}
                        </select>
                    </div>
                )}
            </div>
        </div>
    );
};
