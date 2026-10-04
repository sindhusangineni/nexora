import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
    useAdminAttemptReview,
    useCancelAttempt,
    useEvaluateDescriptive,
} from "@/features/attempts";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { AttemptStatusBadge } from "@/features/attempts/components/AttemptStatusBadge";
import { AlertCircleIcon, BanIcon, CheckIcon } from "@/features/attempts/components/Icons";
import type { EvaluationState } from "@/features/attempts/types/attempt.types";

export const AdminAttemptReviewPage: React.FC = () => {
    const { attemptId } = useParams<{ attemptId: string }>();
    const navigate = useNavigate();

    const {
        data: review,
        isLoading,
        error,
        refetch,
    } = useAdminAttemptReview(attemptId || "");

    const cancelMutation = useCancelAttempt(attemptId || "");
    const evaluateMutation = useEvaluateDescriptive(attemptId || "");

    const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
    const [cancelReason, setCancelReason] = useState("");

    // Evaluation modal state for descriptive item
    const [evaluatingItemId, setEvaluatingItemId] = useState<string | null>(null);
    const [evalState, setEvalState] = useState<EvaluationState>("CORRECT");
    const [marksAwarded, setMarksAwarded] = useState("2.00");
    const [evalComments, setEvalComments] = useState("");

    if (isLoading) {
        return (
            <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-64 w-full rounded-xl" />
            </div>
        );
    }

    if (error || !review) {
        return (
            <div className="max-w-md mx-auto px-4 py-16 text-center">
                <Card className="p-6 space-y-4">
                    <AlertCircleIcon className="w-10 h-10 text-red-500 mx-auto" />
                    <h2 className="text-base font-bold text-neutral-900">Attempt Review Not Found</h2>
                    <p className="text-xs text-foreground-muted">
                        {error?.message || "Unable to load administrative review for this attempt."}
                    </p>
                    <Button size="sm" variant="secondary" onClick={() => navigate("/admin/assessments")}>
                        Back to Assessments
                    </Button>
                </Card>
            </div>
        );
    }

    const handleCancel = async () => {
        if (!cancelReason.trim()) return;
        await cancelMutation.mutateAsync({ reason: cancelReason.trim() });
        setIsCancelModalOpen(false);
        setCancelReason("");
        await refetch();
    };

    const handleEvaluate = async () => {
        if (!evaluatingItemId) return;
        await evaluateMutation.mutateAsync({
            itemId: evaluatingItemId,
            payload: {
                evaluation_state: evalState,
                marks_awarded: marksAwarded,
                evaluation_comments: evalComments.trim() || undefined,
            },
        });
        setEvaluatingItemId(null);
        await refetch();
    };

    return (
        <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                        Attempt Review & Audit
                    </h1>
                    <p className="text-xs text-foreground-muted mt-1">
                        Administrative inspection of student responses, grading status, and attempt session.
                    </p>
                </div>

                <div className="flex items-center space-x-3">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => navigate("/admin/assessments")}
                    >
                        Back to Assessments
                    </Button>

                    {review.status !== "CANCELLED" && (
                        <Button
                            variant="danger"
                            size="sm"
                            onClick={() => setIsCancelModalOpen(true)}
                        >
                            Cancel Attempt
                        </Button>
                    )}
                </div>
            </div>

            {/* Attempt Overview Card */}
            <Card className="p-6 space-y-4 shadow-xs">
                <div className="flex items-center justify-between border-b border-border pb-4">
                    <div>
                        <span className="text-xs font-semibold text-primary uppercase tracking-wider block">
                            Attempt Session #{review.attempt_number}
                        </span>
                        <div className="text-xs text-foreground-muted font-mono mt-0.5">
                            Attempt ID: {review.id}
                        </div>
                    </div>
                    <AttemptStatusBadge status={review.status} />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted font-medium block">Student ID</span>
                        <span className="font-mono text-neutral-900 font-semibold block mt-0.5 truncate">
                            {review.student_id}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted font-medium block">Started At</span>
                        <span className="text-neutral-900 font-semibold block mt-0.5">
                            {new Date(review.started_at).toLocaleTimeString()}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted font-medium block">Expires At</span>
                        <span className="text-neutral-900 font-semibold block mt-0.5">
                            {new Date(review.expires_at).toLocaleTimeString()}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted font-medium block">Submission</span>
                        <span className="text-neutral-900 font-semibold block mt-0.5">
                            {review.submission_reason || (review.submitted_at ? "Completed" : "Active")}
                        </span>
                    </div>
                </div>

                {review.cancellation_reason && (
                    <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-900 flex items-start space-x-2">
                        <BanIcon className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                        <div>
                            <strong>Cancelled:</strong> {review.cancellation_reason}
                        </div>
                    </div>
                )}
            </Card>

            {/* Items and Responses */}
            <div className="space-y-4">
                <h3 className="text-base font-semibold text-foreground tracking-tight">
                    Recorded Attempt Items ({review.items.length})
                </h3>

                {review.items.map((item) => (
                    <Card key={item.id} className="p-5 space-y-3 border-border">
                        <div className="flex items-center justify-between border-b border-border pb-2.5 text-xs">
                            <span className="font-bold text-neutral-900">
                                Question #{item.presentation_order}
                            </span>
                            <div className="flex items-center space-x-2">
                                <span className="text-neutral-500 font-mono">
                                    Allocated: +{item.allocated_marks} / -{item.allocated_penalty}
                                </span>
                                {item.response?.answer_state === "ANSWERED" ? (
                                    <span className="inline-flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-sm font-semibold border border-emerald-200">
                                        Answered
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center text-neutral-500 bg-neutral-100 px-2 py-0.5 rounded-sm font-semibold">
                                        Unanswered
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Student Response Details */}
                        <div className="text-xs space-y-1.5 text-neutral-800">
                            {item.response?.text_response && (
                                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                                    <span className="font-semibold block text-neutral-600 text-[11px] uppercase mb-1">
                                        Student Written Answer:
                                    </span>
                                    <p className="whitespace-pre-line leading-relaxed">
                                        {item.response.text_response}
                                    </p>
                                </div>
                            )}

                            {item.response?.selected_choice_ids && item.response.selected_choice_ids.length > 0 && (
                                <div className="text-xs text-foreground-muted">
                                    Selected choice IDs: {item.response.selected_choice_ids.join(", ")}
                                </div>
                            )}

                            {item.response?.boolean_response !== null && item.response?.boolean_response !== undefined && (
                                <div className="text-xs">
                                    Selected: <strong>{item.response.boolean_response ? "True" : "False"}</strong>
                                </div>
                            )}

                            {item.response?.assertion_reason_response && (
                                <div className="text-xs">
                                    Selected: <strong>{item.response.assertion_reason_response}</strong>
                                </div>
                            )}
                        </div>

                        {/* Evaluation state if exists or evaluation action */}
                        {item.evaluation ? (
                            <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
                                <div className="flex items-center space-x-2">
                                    <CheckIcon className="w-4 h-4 text-emerald-600" />
                                    <span>
                                        Status: <strong>{item.evaluation.evaluation_state}</strong>
                                    </span>
                                    <span>•</span>
                                    <span>
                                        Marks: <strong>{item.evaluation.marks_awarded || "0.00"}</strong>
                                    </span>
                                </div>
                                {item.evaluation.evaluation_comments && (
                                    <span className="text-neutral-500 italic">
                                        "{item.evaluation.evaluation_comments}"
                                    </span>
                                )}
                            </div>
                        ) : (
                            <div className="pt-2 border-t border-border flex justify-end">
                                <Button
                                    size="sm"
                                    variant="secondary"
                                    onClick={() => {
                                        setEvaluatingItemId(item.id);
                                        setMarksAwarded(item.allocated_marks || "2.00");
                                    }}
                                >
                                    Grade / Evaluate Item
                                </Button>
                            </div>
                        )}
                    </Card>
                ))}
            </div>

            {/* Cancel Modal */}
            <Modal
                isOpen={isCancelModalOpen}
                onClose={() => setIsCancelModalOpen(false)}
                title="Cancel Assessment Attempt"
                description="This action will terminate the student's attempt session."
            >
                <div className="space-y-4">
                    <div>
                        <label className="text-xs font-semibold text-neutral-800 block mb-1">
                            Cancellation Reason (Required)
                        </label>
                        <Input
                            type="text"
                            placeholder="e.g. Administrative disqualification, Technical reset"
                            value={cancelReason}
                            onChange={(e) => setCancelReason(e.target.value)}
                        />
                    </div>
                    <div className="flex justify-end space-x-3 pt-3 border-t">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setIsCancelModalOpen(false)}
                        >
                            Back
                        </Button>
                        <Button
                            variant="danger"
                            size="sm"
                            onClick={handleCancel}
                            disabled={!cancelReason.trim() || cancelMutation.isPending}
                        >
                            {cancelMutation.isPending ? "Cancelling..." : "Confirm Cancellation"}
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Evaluate Item Modal */}
            <Modal
                isOpen={!!evaluatingItemId}
                onClose={() => setEvaluatingItemId(null)}
                title="Evaluate Descriptive Item"
                description="Assign marks and evaluation verdict to this student answer."
            >
                <div className="space-y-4">
                    <div>
                        <label className="text-xs font-semibold text-neutral-800 block mb-1">
                            Evaluation Verdict
                        </label>
                        <select
                            value={evalState}
                            onChange={(e) => setEvalState(e.target.value as EvaluationState)}
                            className="w-full px-3 py-2 bg-white border border-border rounded-md text-xs font-medium cursor-pointer"
                        >
                            <option value="CORRECT">CORRECT</option>
                            <option value="PARTIALLY_CORRECT">PARTIALLY_CORRECT</option>
                            <option value="INCORRECT">INCORRECT</option>
                        </select>
                    </div>

                    <div>
                        <label className="text-xs font-semibold text-neutral-800 block mb-1">
                            Marks Awarded
                        </label>
                        <Input
                            type="text"
                            value={marksAwarded}
                            onChange={(e) => setMarksAwarded(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-semibold text-neutral-800 block mb-1">
                            Comments / Rubric notes
                        </label>
                        <Input
                            type="text"
                            placeholder="Optional evaluation feedback"
                            value={evalComments}
                            onChange={(e) => setEvalComments(e.target.value)}
                        />
                    </div>

                    <div className="flex justify-end space-x-3 pt-3 border-t">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setEvaluatingItemId(null)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={handleEvaluate}
                            disabled={evaluateMutation.isPending}
                        >
                            {evaluateMutation.isPending ? "Saving..." : "Submit Grade"}
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};
