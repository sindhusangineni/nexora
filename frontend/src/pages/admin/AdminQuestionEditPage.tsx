import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { parseApiError, type ApiError } from "@/lib/api";
import {
    QuestionForm,
    useCreateQuestionVersion,
    useQuestion,
    useUpdateDraftVersion,
    type BaseQuestionCreatePayload,
} from "@/features/question-bank";

export function AdminQuestionEditPage() {
    const { questionId = "" } = useParams<{ questionId: string }>();
    const navigate = useNavigate();

    const { data: question, isLoading, isError } = useQuestion(questionId);

    const [apiError, setApiError] = useState<ApiError | null>(null);

    const latestVersion = question?.latest_version;
    const isDraft = latestVersion?.status === "DRAFT";

    const updateMutation = useUpdateDraftVersion(
        questionId,
        latestVersion?.id || "",
    );
    const createVersionMutation = useCreateQuestionVersion(questionId);

    const handleUpdateDraft = async (payload: BaseQuestionCreatePayload) => {
        setApiError(null);
        try {
            await updateMutation.mutateAsync(payload);
            navigate(`/admin/question-bank/questions/${questionId}`);
        } catch (err) {
            setApiError(parseApiError(err));
        }
    };

    const handleCreateFork = async () => {
        if (!latestVersion) return;
        setApiError(null);
        try {
            const payload: BaseQuestionCreatePayload = {
                question_type: latestVersion.question_type,
                text: latestVersion.text,
                difficulty: latestVersion.difficulty,
                explanation: latestVersion.explanation || "",
                topic_ids: question?.topic_ids || [],
                source_type: latestVersion.source_type || null,
                source_name: latestVersion.source_name || null,
                source_reference: latestVersion.source_reference || null,
                source_year: latestVersion.source_year || null,
                external_question_id: latestVersion.external_question_id || null,
                choices: latestVersion.content?.choices?.map((c) => ({
                    text: c.text,
                    position: c.position,
                    is_correct: c.is_correct,
                })),
                true_false:
                    latestVersion.content?.answer !== undefined &&
                    latestVersion.content?.answer !== null
                        ? { answer: latestVersion.content.answer }
                        : undefined,
                assertion_reason:
                    latestVersion.content?.assertion && latestVersion.content?.reason
                        ? {
                              assertion: latestVersion.content.assertion,
                              reason: latestVersion.content.reason,
                              correct_relationship:
                                  latestVersion.content.correct_relationship!,
                          }
                        : undefined,
                match_following:
                    latestVersion.content?.left_items &&
                    latestVersion.content?.right_items &&
                    latestVersion.content?.pairs
                        ? {
                              left_items: latestVersion.content.left_items.map((i) => ({
                                  text: i.text,
                                  position: i.position,
                              })),
                              right_items: latestVersion.content.right_items.map((i) => ({
                                  text: i.text,
                                  position: i.position,
                              })),
                              pairs: latestVersion.content.pairs.map((p) => ({
                                  left_position: p.left_position,
                                  right_position: p.right_position,
                              })),
                          }
                        : undefined,
                descriptive:
                    latestVersion.content?.marks &&
                    latestVersion.content?.expected_answer
                        ? {
                              marks: latestVersion.content.marks,
                              expected_answer: latestVersion.content.expected_answer,
                          }
                        : undefined,
            };

            await createVersionMutation.mutateAsync(payload);
            navigate(`/admin/question-bank/questions/${questionId}`);
        } catch (err) {
            setApiError(parseApiError(err));
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-6 max-w-4xl mx-auto p-6">
                <Skeleton height={32} className="w-48" />
                <Skeleton height={200} className="w-full" />
            </div>
        );
    }

    if (isError || !question) {
        return (
            <div className="p-8 text-center space-y-4">
                <p className="text-base font-semibold text-danger">
                    Question record not found.
                </p>
                <Link to="/admin/question-bank">
                    <Button variant="secondary" size="sm">
                        ← Return to Question Bank
                    </Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-4xl mx-auto pb-12">
            {/* Header */}
            <div className="space-y-2 pb-4 border-b border-border">
                <Link
                    to={`/admin/question-bank/questions/${questionId}`}
                    className="inline-flex items-center text-xs font-semibold text-primary-600 hover:text-primary-800"
                >
                    ← Back to Question Details
                </Link>
                <div className="flex items-center gap-2 pt-1">
                    <span className="font-mono text-sm font-bold text-neutral-800 px-2 py-0.5 rounded bg-neutral-100 border border-neutral-200">
                        Question: {question.id.slice(0, 8)}
                    </span>
                    {latestVersion && (
                        <Badge
                            variant={isDraft ? "default" : "warning"}
                            size="sm"
                        >
                            v{latestVersion.version_number} ({latestVersion.status})
                        </Badge>
                    )}
                </div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                    {isDraft ? "Edit Draft Version" : "Version Modification"}
                </h1>
            </div>

            {apiError && (
                <div
                    role="alert"
                    className="p-4 rounded-xl bg-red-50 border border-red-200 text-danger text-sm font-medium"
                >
                    <p className="font-semibold">{apiError.message}</p>
                    {apiError.fields && (
                        <ul className="mt-1 text-xs list-disc list-inside space-y-0.5">
                            {Object.entries(apiError.fields).map(([field, msgs]) => (
                                <li key={field}>
                                    <span className="font-semibold capitalize">{field}</span>:{" "}
                                    {msgs.join(" ")}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}

            {isDraft && latestVersion ? (
                <QuestionForm
                    initialData={{
                        question_type: latestVersion.question_type,
                        text: latestVersion.text,
                        difficulty: latestVersion.difficulty,
                        explanation: latestVersion.explanation || "",
                        topic_ids: question.topic_ids || [],
                        source_type: latestVersion.source_type,
                        source_name: latestVersion.source_name || "",
                        source_reference: latestVersion.source_reference || "",
                        source_year: latestVersion.source_year,
                        external_question_id:
                            latestVersion.external_question_id || "",
                        choices: latestVersion.content?.choices,
                        true_false:
                            latestVersion.content?.answer !== undefined &&
                            latestVersion.content?.answer !== null
                                ? { answer: latestVersion.content.answer }
                                : undefined,
                        assertion_reason:
                            latestVersion.content?.assertion &&
                            latestVersion.content?.reason
                                ? {
                                      assertion: latestVersion.content.assertion,
                                      reason: latestVersion.content.reason,
                                      correct_relationship:
                                          latestVersion.content.correct_relationship!,
                                  }
                                : undefined,
                        match_following:
                            latestVersion.content?.left_items &&
                            latestVersion.content?.right_items &&
                            latestVersion.content?.pairs
                                ? {
                                      left_items: latestVersion.content.left_items,
                                      right_items: latestVersion.content.right_items,
                                      pairs: latestVersion.content.pairs,
                                  }
                                : undefined,
                        descriptive:
                            latestVersion.content?.marks &&
                            latestVersion.content?.expected_answer
                                ? {
                                      marks: latestVersion.content.marks,
                                      expected_answer:
                                          latestVersion.content.expected_answer,
                                  }
                                : undefined,
                    }}
                    onSubmit={handleUpdateDraft}
                    isSubmitting={updateMutation.isPending}
                    submitLabel="Save Changes to Draft"
                    isEditingDraft={true}
                />
            ) : (
                <Card>
                    <CardHeader>
                        <CardTitle>This Version Cannot Be Modified</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-foreground-muted leading-relaxed">
                            Version <strong>v{latestVersion?.version_number}</strong> is currently{" "}
                            <strong>{latestVersion?.status}</strong>. To guarantee test integrity,
                            published and approved versions cannot be mutated in place.
                        </p>
                        <p className="text-sm text-foreground-muted leading-relaxed">
                            To propose corrections, initialize a new editorial version. It will start
                            as a DRAFT containing this version's content.
                        </p>

                        <div className="pt-2 flex items-center gap-3">
                            <Button
                                variant="primary"
                                size="md"
                                loading={createVersionMutation.isPending}
                                disabled={createVersionMutation.isPending}
                                onClick={handleCreateFork}
                            >
                                + Create Version v{(latestVersion?.version_number || 1) + 1} Draft
                            </Button>
                            <Link to={`/admin/question-bank/questions/${questionId}`}>
                                <Button variant="secondary" size="md">
                                    Cancel
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
