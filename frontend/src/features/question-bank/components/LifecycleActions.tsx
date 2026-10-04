import { useState } from "react";

import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { parseApiError, type ApiError } from "@/lib/api";
import {
    useApproveVersion,
    useArchiveVersion,
    usePublishVersion,
    useSubmitReview,
} from "../hooks/useQuestionBank";
import type { QuestionStatus } from "../types/questionBank.types";

export interface LifecycleActionsProps {
    questionId: string;
    versionId: string;
    versionNumber: number;
    status: QuestionStatus;
    onCreateNewVersion?: () => void;
    onStatusChange?: (newStatus: QuestionStatus) => void;
}

type ActionType = "submit-review" | "approve" | "publish" | "archive";

export function LifecycleActions({
    questionId,
    versionId,
    versionNumber,
    status,
    onCreateNewVersion,
}: LifecycleActionsProps) {
    const [activeModal, setActiveModal] = useState<ActionType | null>(null);
    const [apiError, setApiError] = useState<ApiError | null>(null);

    const submitReviewMutation = useSubmitReview(questionId);
    const approveMutation = useApproveVersion(questionId);
    const publishMutation = usePublishVersion(questionId);
    const archiveMutation = useArchiveVersion(questionId);

    const isPending =
        submitReviewMutation.isPending ||
        approveMutation.isPending ||
        publishMutation.isPending ||
        archiveMutation.isPending;

    const handleConfirm = async () => {
        setApiError(null);
        try {
            if (activeModal === "submit-review") {
                await submitReviewMutation.mutateAsync(versionId);
            } else if (activeModal === "approve") {
                await approveMutation.mutateAsync(versionId);
            } else if (activeModal === "publish") {
                await publishMutation.mutateAsync(versionId);
            } else if (activeModal === "archive") {
                await archiveMutation.mutateAsync(versionId);
            }
            setActiveModal(null);
        } catch (err) {
            setApiError(parseApiError(err));
        }
    };

    const modalConfigs: Record<
        ActionType,
        {
            title: string;
            description: string;
            confirmLabel: string;
            variant: "primary" | "danger" | "secondary";
        }
    > = {
        "submit-review": {
            title: `Submit Version v${versionNumber} for Review`,
            description:
                "This will change the status to 'Under Review'. Authors will not be able to edit this version while it is being reviewed.",
            confirmLabel: "Submit for Review",
            variant: "primary",
        },
        approve: {
            title: `Approve Version v${versionNumber}`,
            description:
                "Confirm that this question version satisfies academic accuracy, formatting guidelines, and evaluation rubrics. Once approved, it can be published.",
            confirmLabel: "Approve Version",
            variant: "primary",
        },
        publish: {
            title: `Publish Version v${versionNumber}`,
            description:
                "Publishing will make this version the active authoritative version for candidate assessments. If another version was previously published, it will be superseded.",
            confirmLabel: "Publish Now",
            variant: "primary",
        },
        archive: {
            title: `Archive Version v${versionNumber}`,
            description:
                "Archiving decommissions this question version. It will no longer be eligible for inclusion in future test paper blueprints.",
            confirmLabel: "Archive Version",
            variant: "danger",
        },
    };

    const currentConfig = activeModal ? modalConfigs[activeModal] : null;

    return (
        <div className="flex flex-wrap items-center gap-2.5">
            {status === "DRAFT" && (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                        setApiError(null);
                        setActiveModal("submit-review");
                    }}
                >
                    Submit for Review
                </Button>
            )}

            {status === "REVIEW" && (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                        setApiError(null);
                        setActiveModal("approve");
                    }}
                >
                    Approve Version
                </Button>
            )}

            {status === "APPROVED" && (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                        setApiError(null);
                        setActiveModal("publish");
                    }}
                >
                    Publish Version
                </Button>
            )}

            {status === "PUBLISHED" && (
                <Button
                    variant="secondary"
                    size="sm"
                    className="text-danger hover:bg-red-50 border-red-200"
                    onClick={() => {
                        setApiError(null);
                        setActiveModal("archive");
                    }}
                >
                    Archive Version
                </Button>
            )}

            {onCreateNewVersion && status !== "DRAFT" && (
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={onCreateNewVersion}
                >
                    + Create New Version
                </Button>
            )}

            {/* Confirmation Modal */}
            {activeModal && currentConfig && (
                <Modal
                    isOpen={true}
                    onClose={() => {
                        if (!isPending) {
                            setActiveModal(null);
                            setApiError(null);
                        }
                    }}
                    title={currentConfig.title}
                    description={currentConfig.description}
                >
                    <div className="space-y-4 pt-2">
                        {apiError && (
                            <div
                                role="alert"
                                className="p-3 text-sm rounded-lg bg-red-50 border border-red-200 text-danger"
                            >
                                <p className="font-medium">{apiError.message}</p>
                            </div>
                        )}

                        <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
                            <Button
                                variant="secondary"
                                size="md"
                                onClick={() => {
                                    setActiveModal(null);
                                    setApiError(null);
                                }}
                                disabled={isPending}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant={currentConfig.variant}
                                size="md"
                                loading={isPending}
                                disabled={isPending}
                                onClick={handleConfirm}
                            >
                                {currentConfig.confirmLabel}
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}
