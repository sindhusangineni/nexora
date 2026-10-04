import React from "react";
import { Modal } from "@/shared/ui/Modal";
import { Button } from "@/shared/ui/Button";
import { AlertCircleIcon } from "./Icons";

interface SubmitAttemptModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    totalQuestions: number;
    answeredQuestions: number;
    isSubmitting?: boolean;
}

export const SubmitAttemptModal: React.FC<SubmitAttemptModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    totalQuestions,
    answeredQuestions,
    isSubmitting = false,
}) => {
    const unansweredQuestions = Math.max(0, totalQuestions - answeredQuestions);

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Submit Assessment"
            description="Please review your submission summary before finalizing."
            maxWidth="md"
        >
            <div className="space-y-5">
                <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                        <span className="text-xl font-bold text-emerald-700 block">
                            {answeredQuestions}
                        </span>
                        <span className="text-xs text-emerald-800 font-medium">
                            Answered
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-xl font-bold text-neutral-800 block">
                            {unansweredQuestions}
                        </span>
                        <span className="text-xs text-foreground-muted font-medium">
                            Unanswered
                        </span>
                    </div>
                </div>

                {unansweredQuestions > 0 && (
                    <div className="flex items-start space-x-2.5 p-3.5 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-800">
                        <AlertCircleIcon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                            <strong>You have {unansweredQuestions} unanswered {unansweredQuestions === 1 ? "question" : "questions"}.</strong>
                            <p className="mt-0.5 text-amber-700">
                                You can submit now or go back to answer remaining questions.
                            </p>
                        </div>
                    </div>
                )}

                <p className="text-xs text-foreground-muted">
                    Once submitted, your responses are finalized and cannot be modified.
                </p>

                <div className="flex items-center justify-end space-x-3 pt-3 border-t border-border">
                    <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={onClose}
                        disabled={isSubmitting}
                    >
                        Back to Test
                    </Button>
                    <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={onConfirm}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? "Submitting..." : "Confirm & Submit"}
                    </Button>
                </div>
            </div>
        </Modal>
    );
};
