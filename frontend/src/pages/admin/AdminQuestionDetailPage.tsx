import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { Modal } from "@/shared/ui/Modal";
import { parseApiError, type ApiError } from "@/lib/api";
import {
    LifecycleActions,
    QuestionStatusBadge,
    VersionHistoryList,
    useCreateQuestionVersion,
    useQuestion,
    useQuestionVersion,
    useQuestionVersions,
    type QuestionVersionAdminResponse,
} from "@/features/question-bank";

export function AdminQuestionDetailPage() {
    const { questionId = "" } = useParams<{ questionId: string }>();
    const navigate = useNavigate();

    const {
        data: question,
        isLoading: isQuestionLoading,
        isError: isQuestionError,
    } = useQuestion(questionId);

    const { data: versionsData, isLoading: isVersionsLoading } =
        useQuestionVersions(questionId);

    const [selectedVersionId, setSelectedVersionId] = useState<string>("");
    const [isCreateVersionOpen, setIsCreateVersionOpen] = useState(false);
    const [createVersionError, setCreateVersionError] = useState<ApiError | null>(
        null,
    );

    const createVersionMutation = useCreateQuestionVersion(questionId);

    const effectiveVersionId =
        selectedVersionId ||
        question?.latest_version?.id ||
        question?.published_version?.id ||
        "";

    const {
        data: activeVersion,
        isLoading: isVersionLoading,
    } = useQuestionVersion(questionId, effectiveVersionId);

    const handleCreateNewVersion = async () => {
        if (!activeVersion) return;
        setCreateVersionError(null);
        try {
            const payload = {
                question_type: activeVersion.question_type,
                text: activeVersion.text,
                difficulty: activeVersion.difficulty,
                explanation: activeVersion.explanation || "",
                topic_ids: question?.topic_ids || [],
                source_type: activeVersion.source_type || null,
                source_name: activeVersion.source_name || null,
                source_reference: activeVersion.source_reference || null,
                source_year: activeVersion.source_year || null,
                external_question_id: activeVersion.external_question_id || null,
                choices: activeVersion.content?.choices?.map((c) => ({
                    text: c.text,
                    position: c.position,
                    is_correct: c.is_correct,
                })),
                true_false:
                    activeVersion.content?.answer !== undefined &&
                    activeVersion.content?.answer !== null
                        ? { answer: activeVersion.content.answer }
                        : undefined,
                assertion_reason:
                    activeVersion.content?.assertion && activeVersion.content?.reason
                        ? {
                              assertion: activeVersion.content.assertion,
                              reason: activeVersion.content.reason,
                              correct_relationship:
                                  activeVersion.content.correct_relationship!,
                          }
                        : undefined,
                match_following:
                    activeVersion.content?.left_items &&
                    activeVersion.content?.right_items &&
                    activeVersion.content?.pairs
                        ? {
                              left_items: activeVersion.content.left_items.map((i) => ({
                                  text: i.text,
                                  position: i.position,
                              })),
                              right_items: activeVersion.content.right_items.map((i) => ({
                                  text: i.text,
                                  position: i.position,
                              })),
                              pairs: activeVersion.content.pairs.map((p) => ({
                                  left_position: p.left_position,
                                  right_position: p.right_position,
                              })),
                          }
                        : undefined,
                descriptive:
                    activeVersion.content?.marks &&
                    activeVersion.content?.expected_answer
                        ? {
                              marks: activeVersion.content.marks,
                              expected_answer: activeVersion.content.expected_answer,
                          }
                        : undefined,
            };

            const newVersion = await createVersionMutation.mutateAsync(payload);
            setIsCreateVersionOpen(false);
            setSelectedVersionId(newVersion.id);
            navigate(`/admin/question-bank/questions/${questionId}/edit`);
        } catch (err) {
            setCreateVersionError(parseApiError(err));
        }
    };

    if (isQuestionLoading) {
        return (
            <div className="space-y-6 max-w-7xl mx-auto p-6">
                <Skeleton height={32} className="w-48" />
                <Skeleton height={200} className="w-full" />
                <Skeleton height={300} className="w-full" />
            </div>
        );
    }

    if (isQuestionError || !question) {
        return (
            <div className="p-8 text-center space-y-4">
                <p className="text-base font-semibold text-danger">
                    Question record not found or server error.
                </p>
                <Link to="/admin/question-bank">
                    <Button variant="secondary" size="sm">
                        ← Return to Question Bank
                    </Button>
                </Link>
            </div>
        );
    }

    const versionToDisplay = activeVersion || question.latest_version;
    const isDraft = versionToDisplay?.status === "DRAFT";
    const isImmutable = !isDraft;

    const optionLetters = ["A", "B", "C", "D", "E", "F", "G", "H"];

    return (
        <div className="space-y-6 max-w-7xl mx-auto pb-16">
            {/* Top Navigation & Breadcrumbs */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div className="space-y-1">
                    <Link
                        to="/admin/question-bank"
                        className="inline-flex items-center text-xs font-semibold text-primary-600 hover:text-primary-800"
                    >
                        ← Back to Question Bank
                    </Link>
                    <div className="flex flex-wrap items-center gap-2.5 pt-1">
                        <span className="font-mono text-sm font-bold text-neutral-800 px-2 py-0.5 rounded bg-neutral-100 border border-neutral-200">
                            Question: {question.id.slice(0, 8)}
                        </span>
                        {versionToDisplay && (
                            <QuestionStatusBadge status={versionToDisplay.status} size="sm" />
                        )}
                        <Badge variant="outline" size="sm">
                            {versionToDisplay?.question_type}
                        </Badge>
                        <Badge
                            variant={
                                versionToDisplay?.difficulty === "HARD"
                                    ? "danger"
                                    : versionToDisplay?.difficulty === "MEDIUM"
                                    ? "warning"
                                    : "success"
                            }
                            size="sm"
                        >
                            {versionToDisplay?.difficulty}
                        </Badge>
                    </div>
                </div>

                {/* Top Action Bar */}
                <div className="flex items-center gap-3">
                    {isDraft ? (
                        <Link to={`/admin/question-bank/questions/${questionId}/edit`}>
                            <Button variant="secondary" size="md">
                                Edit Draft
                            </Button>
                        </Link>
                    ) : (
                        <Button
                            variant="secondary"
                            size="md"
                            onClick={() => setIsCreateVersionOpen(true)}
                        >
                            + New Version
                        </Button>
                    )}

                    {versionToDisplay && (
                        <LifecycleActions
                            questionId={question.id}
                            versionId={versionToDisplay.id}
                            versionNumber={versionToDisplay.version_number}
                            status={versionToDisplay.status}
                            onCreateNewVersion={() => setIsCreateVersionOpen(true)}
                        />
                    )}
                </div>
            </div>

            {/* Immutability Banner for Published/Approved/Archived versions */}
            {isImmutable && (
                <div
                    className="p-4 rounded-xl border border-primary-200 bg-primary-50/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs"
                    role="note"
                >
                    <div className="flex items-center gap-2.5 text-primary-950 font-medium">
                        <span className="w-5 h-5 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center font-bold text-xs shrink-0">
                            ℹ
                        </span>
                        <span>
                            Version <strong>v{versionToDisplay?.version_number}</strong> is{" "}
                            <strong>{versionToDisplay?.status}</strong> and immutable. To make
                            modifications, initialize a new editorial version.
                        </span>
                    </div>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setIsCreateVersionOpen(true)}
                    >
                        Create Version v{(versionToDisplay?.version_number || 1) + 1}
                    </Button>
                </div>
            )}

            {/* Main Layout Grid: Detail View (8 cols) + Version History Sidebar (4 cols) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                {/* Left Detail Column */}
                <div className="lg:col-span-8 space-y-6">
                    {/* Stem & Core Content Card */}
                    <Card>
                        <CardHeader className="pb-3 border-b border-border/80">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-neutral-500">
                                    Version v{versionToDisplay?.version_number} Content
                                </span>
                                <div className="flex items-center gap-2">
                                    {isVersionLoading && (
                                        <span className="text-xs text-primary-600 animate-pulse font-medium">
                                            Loading version...
                                        </span>
                                    )}
                                    <span className="text-xs text-foreground-muted font-mono">
                                        UUID: {versionToDisplay?.id.slice(0, 8)}...
                                    </span>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-5 space-y-6">
                            {/* Stem Text */}
                            <div>
                                <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2">
                                    Question Stem
                                </h3>
                                <p className="text-base font-medium text-foreground leading-relaxed whitespace-pre-wrap">
                                    {versionToDisplay?.text}
                                </p>
                            </div>

                            {/* Type Specific Admin Content & Answer Key */}
                            <div className="pt-4 border-t border-border">
                                <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-3">
                                    Answer Key & Structured Options
                                </h3>

                                {/* MCQ / MULTIPLE_SELECT */}
                                {(versionToDisplay?.question_type === "MCQ" ||
                                    versionToDisplay?.question_type === "MULTIPLE_SELECT") &&
                                    versionToDisplay.content?.choices && (
                                        <div className="space-y-2.5">
                                            {versionToDisplay.content.choices.map((c, idx) => {
                                                const label = optionLetters[idx] || `${idx + 1}`;
                                                const isCorrect = Boolean(c.is_correct);

                                                return (
                                                    <div
                                                        key={c.id || idx}
                                                        className={`flex items-start justify-between gap-3 p-3.5 rounded-lg border ${
                                                            isCorrect
                                                                ? "bg-emerald-50/70 border-emerald-300 ring-1 ring-emerald-300"
                                                                : "bg-surface border-border"
                                                        }`}
                                                    >
                                                        <div className="flex items-start gap-3">
                                                            <span
                                                                className={`w-6 h-6 rounded font-bold text-xs flex items-center justify-center shrink-0 ${
                                                                    isCorrect
                                                                        ? "bg-emerald-600 text-white"
                                                                        : "bg-neutral-100 text-neutral-700"
                                                                }`}
                                                            >
                                                                {label}
                                                            </span>
                                                            <span className="text-sm text-foreground pt-0.5">
                                                                {c.text}
                                                            </span>
                                                        </div>
                                                        {isCorrect && (
                                                            <span className="text-xs font-bold text-emerald-700 shrink-0 mt-0.5">
                                                                ✓ Correct Answer
                                                            </span>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}

                                {/* TRUE_FALSE */}
                                {versionToDisplay?.question_type === "TRUE_FALSE" && (
                                    <div className="p-4 rounded-xl border border-border bg-surface-muted/40 flex items-center gap-4">
                                        <span className="text-xs font-semibold text-neutral-600">
                                            Authoritative Truth Value:
                                        </span>
                                        <Badge
                                            variant={
                                                versionToDisplay.content?.answer ? "success" : "danger"
                                            }
                                            size="md"
                                        >
                                            {versionToDisplay.content?.answer ? "TRUE" : "FALSE"}
                                        </Badge>
                                    </div>
                                )}

                                {/* ASSERTION_REASON */}
                                {versionToDisplay?.question_type === "ASSERTION_REASON" && (
                                    <div className="space-y-3">
                                        <div className="p-3.5 rounded-lg bg-surface-muted border border-border space-y-1">
                                            <span className="text-xs font-bold uppercase text-primary-700 block">
                                                Assertion (A)
                                            </span>
                                            <p className="text-sm text-foreground">
                                                {versionToDisplay.content?.assertion}
                                            </p>
                                        </div>
                                        <div className="p-3.5 rounded-lg bg-surface-muted border border-border space-y-1">
                                            <span className="text-xs font-bold uppercase text-primary-700 block">
                                                Reason (R)
                                            </span>
                                            <p className="text-sm text-foreground">
                                                {versionToDisplay.content?.reason}
                                            </p>
                                        </div>
                                        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200">
                                            <span className="text-xs font-bold uppercase text-emerald-800 block mb-1">
                                                Correct Relationship
                                            </span>
                                            <span className="text-xs font-semibold text-emerald-950">
                                                {versionToDisplay.content?.correct_relationship}
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* MATCH_FOLLOWING */}
                                {versionToDisplay?.question_type === "MATCH_FOLLOWING" &&
                                    versionToDisplay.content?.left_items &&
                                    versionToDisplay.content?.right_items && (
                                        <div className="space-y-4">
                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                                <div className="p-3.5 rounded-lg border border-border bg-surface-muted space-y-2">
                                                    <span className="text-xs font-bold uppercase text-neutral-500 block">
                                                        Column I
                                                    </span>
                                                    {versionToDisplay.content.left_items.map((i) => (
                                                        <div key={i.id} className="text-xs flex gap-2">
                                                            <span className="font-bold text-neutral-700">
                                                                {i.position}.
                                                            </span>
                                                            <span>{i.text}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                                <div className="p-3.5 rounded-lg border border-border bg-surface-muted space-y-2">
                                                    <span className="text-xs font-bold uppercase text-neutral-500 block">
                                                        Column II
                                                    </span>
                                                    {versionToDisplay.content.right_items.map(
                                                        (i, idx) => (
                                                            <div key={i.id} className="text-xs flex gap-2">
                                                                <span className="font-bold text-neutral-700">
                                                                    {optionLetters[idx] || i.position}.
                                                                </span>
                                                                <span>{i.text}</span>
                                                            </div>
                                                        ),
                                                    )}
                                                </div>
                                            </div>

                                            {versionToDisplay.content.pairs && (
                                                <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/60">
                                                    <span className="text-xs font-bold uppercase text-emerald-800 block mb-1">
                                                        Verified Match Pairs
                                                    </span>
                                                    <div className="flex flex-wrap gap-3 text-xs font-mono font-semibold text-emerald-950">
                                                        {versionToDisplay.content.pairs.map((p, idx) => (
                                                            <span
                                                                key={idx}
                                                                className="px-2 py-1 rounded bg-emerald-100 border border-emerald-200"
                                                            >
                                                                Item {p.left_position} →{" "}
                                                                {optionLetters[p.right_position - 1] ||
                                                                    p.right_position}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                {/* DESCRIPTIVE */}
                                {versionToDisplay?.question_type === "DESCRIPTIVE" &&
                                    versionToDisplay.content && (
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-2 text-xs">
                                                <span className="font-semibold text-neutral-700">
                                                    Allocated Marks:
                                                </span>
                                                <Badge variant="primary" size="sm">
                                                    {versionToDisplay.content.marks} Marks
                                                </Badge>
                                            </div>
                                            <div className="p-4 rounded-xl border border-border bg-surface-muted space-y-1">
                                                <span className="text-xs font-bold uppercase text-neutral-500 block">
                                                    Reference Rubric & Benchmark Answer
                                                </span>
                                                <p className="text-xs text-foreground leading-relaxed whitespace-pre-wrap">
                                                    {versionToDisplay.content.expected_answer}
                                                </p>
                                            </div>
                                        </div>
                                    )}
                            </div>

                            {/* Pedagogical Explanation */}
                            {versionToDisplay?.explanation && (
                                <div className="pt-4 border-t border-border space-y-1.5">
                                    <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500">
                                        Pedagogical Explanation
                                    </h3>
                                    <div className="p-4 rounded-xl border border-border bg-surface-muted/40 text-xs text-foreground leading-relaxed whitespace-pre-wrap">
                                        {versionToDisplay.explanation}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Provenance Metadata Card (if present) */}
                    {(versionToDisplay?.source_name ||
                        versionToDisplay?.source_type ||
                        versionToDisplay?.source_reference ||
                        versionToDisplay?.source_year) && (
                        <Card>
                            <CardHeader className="pb-3 border-b border-border">
                                <CardTitle className="text-sm font-semibold">
                                    Provenance & Citation
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                                <div>
                                    <span className="text-foreground-muted block">Source Type</span>
                                    <span className="font-semibold text-neutral-900">
                                        {versionToDisplay.source_type || "—"}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-foreground-muted block">Source Name</span>
                                    <span className="font-semibold text-neutral-900">
                                        {versionToDisplay.source_name || "—"}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-foreground-muted block">Year</span>
                                    <span className="font-semibold text-neutral-900">
                                        {versionToDisplay.source_year || "—"}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-foreground-muted block">Reference</span>
                                    <span className="font-semibold text-neutral-900">
                                        {versionToDisplay.source_reference || "—"}
                                    </span>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Right Column: Version History Sidebar */}
                <div className="lg:col-span-4 space-y-6">
                    <Card>
                        <CardContent className="p-4">
                            {isVersionsLoading ? (
                                <div className="space-y-3">
                                    <Skeleton height={30} className="w-full" />
                                    <Skeleton height={50} className="w-full" />
                                    <Skeleton height={50} className="w-full" />
                                </div>
                            ) : versionsData?.results ? (
                                <VersionHistoryList
                                    versions={versionsData.results}
                                    selectedVersionId={versionToDisplay?.id || ""}
                                    publishedVersionId={question.published_version?.id}
                                    onSelectVersion={(v: QuestionVersionAdminResponse) =>
                                        setSelectedVersionId(v.id)
                                    }
                                />
                            ) : null}
                        </CardContent>
                    </Card>

                    {/* Operational Details Card */}
                    <Card>
                        <CardHeader className="pb-2 border-b border-border">
                            <CardTitle className="text-xs uppercase tracking-wider text-neutral-500">
                                Question Aggregate Info
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-3 space-y-2.5 text-xs">
                            <div className="flex justify-between">
                                <span className="text-foreground-muted">Total Versions:</span>
                                <span className="font-mono font-bold text-neutral-900">
                                    {question.version_count}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-foreground-muted">Published Version:</span>
                                <span className="font-mono font-bold text-neutral-900">
                                    {question.published_version
                                        ? `v${question.published_version.version_number}`
                                        : "None"}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-foreground-muted">Associated Topics:</span>
                                <span className="font-semibold text-neutral-900">
                                    {question.topic_ids?.length || 0}
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Modal for Creating New Version */}
            {isCreateVersionOpen && (
                <Modal
                    isOpen={true}
                    onClose={() => {
                        if (!createVersionMutation.isPending) {
                            setIsCreateVersionOpen(false);
                            setCreateVersionError(null);
                        }
                    }}
                    title={`Create New Version v${(versionToDisplay?.version_number || 1) + 1}`}
                    description="This will fork the current version's text and options into a new DRAFT version. You can then edit the draft before submitting it for review."
                >
                    <div className="space-y-4 pt-2">
                        {createVersionError && (
                            <div
                                role="alert"
                                className="p-3 text-sm rounded-lg bg-red-50 border border-red-200 text-danger"
                            >
                                <p className="font-medium">{createVersionError.message}</p>
                            </div>
                        )}

                        <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
                            <Button
                                variant="secondary"
                                size="md"
                                onClick={() => {
                                    setIsCreateVersionOpen(false);
                                    setCreateVersionError(null);
                                }}
                                disabled={createVersionMutation.isPending}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="primary"
                                size="md"
                                loading={createVersionMutation.isPending}
                                disabled={createVersionMutation.isPending}
                                onClick={handleCreateNewVersion}
                            >
                                Create Draft Version
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}
