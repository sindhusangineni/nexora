import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import {
    useArchiveAssessment,
    useGeneratePaper,
    usePublishAssessment,
} from "../hooks/useAssessment";
import type { Assessment, SelectionRule } from "../types/assessment.types";

interface AssessmentLifecycleActionsProps {
    assessment: Assessment;
    rules: SelectionRule[];
    onPaperGenerated?: (paperId: string) => void;
}

export const AssessmentLifecycleActions: React.FC<AssessmentLifecycleActionsProps> = ({
    assessment,
    rules,
    onPaperGenerated,
}) => {
    const navigate = useNavigate();
    const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
    const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false);
    const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);

    const publishMutation = usePublishAssessment();
    const archiveMutation = useArchiveAssessment();
    const generatePaperMutation = useGeneratePaper(assessment.id);

    const isDraft = assessment.status === "DRAFT";
    const isPublished = assessment.status === "PUBLISHED";
    const isArchived = assessment.status === "ARCHIVED";

    const hasRules = rules.length > 0;
    const canPublish = isDraft && hasRules;

    const handlePublish = async () => {
        setActionError(null);
        try {
            await publishMutation.mutateAsync(assessment.id);
            setIsPublishModalOpen(false);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to publish assessment.";
            setActionError(message);
        }
    };

    const handleArchive = async () => {
        setActionError(null);
        try {
            await archiveMutation.mutateAsync(assessment.id);
            setIsArchiveModalOpen(false);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to archive assessment.";
            setActionError(message);
        }
    };

    const handleGeneratePaper = async () => {
        setActionError(null);
        try {
            const paper = await generatePaperMutation.mutateAsync();
            setIsGenerateModalOpen(false);
            if (onPaperGenerated) {
                onPaperGenerated(paper.id);
            } else {
                navigate(`/admin/assessments/${assessment.id}/paper?paperId=${paper.id}`);
            }
        } catch (err: unknown) {
            const message =
                err instanceof Error ? err.message : "Failed to generate assessment paper.";
            setActionError(message);
        }
    };

    return (
        <div className="space-y-3">
            {actionError && (
                <div className="p-3 text-xs text-danger bg-danger-surface rounded-md border border-danger/20">
                    {actionError}
                </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
                {/* DRAFT Actions */}
                {isDraft && (
                    <>
                        <Button
                            variant="primary"
                            size="sm"
                            disabled={!canPublish}
                            onClick={() => {
                                setActionError(null);
                                setIsPublishModalOpen(true);
                            }}
                            aria-label="Publish Assessment"
                        >
                            Publish Assessment
                        </Button>
                        {!hasRules && (
                            <span className="text-xs text-foreground-muted">
                                Add at least 1 selection rule to publish
                            </span>
                        )}
                    </>
                )}

                {/* PUBLISHED Actions */}
                {isPublished && (
                    <>
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                                setActionError(null);
                                setIsGenerateModalOpen(true);
                            }}
                            aria-label="Generate Assessment Paper"
                        >
                            Generate Assessment Paper
                        </Button>

                        <Button
                            variant="danger"
                            size="sm"
                            onClick={() => {
                                setActionError(null);
                                setIsArchiveModalOpen(true);
                            }}
                            aria-label="Archive Assessment"
                        >
                            Archive Assessment
                        </Button>
                    </>
                )}

                {/* ARCHIVED Notice */}
                {isArchived && (
                    <div className="text-xs text-foreground-muted italic">
                        This assessment is archived and permanently immutable.
                    </div>
                )}
            </div>

            {/* Immutability Banner for Published Assessments */}
            {isPublished && (
                <div className="p-3 bg-neutral-50 border border-neutral-200 rounded-md text-xs text-foreground-muted">
                    <span className="font-semibold text-neutral-800">Published Assessment: </span>
                    Configuration, sections, and selection rules are locked to guarantee integrity. You can generate immutable test papers from this specification.
                </div>
            )}

            {/* Publish Confirmation Modal */}
            <Modal
                isOpen={isPublishModalOpen}
                onClose={() => setIsPublishModalOpen(false)}
                title="Publish Assessment"
            >
                <div className="space-y-4">
                    <p className="text-sm text-foreground-muted">
                        Publishing locks the assessment definition, including duration, marking configuration, sections, and selection rules. Once published, the assessment configuration becomes immutable and test papers can be generated.
                    </p>
                    <p className="text-xs font-semibold text-neutral-700">
                        Are you sure you want to transition this assessment to PUBLISHED?
                    </p>
                    <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                        <Button
                            variant="secondary"
                            onClick={() => setIsPublishModalOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="primary"
                            loading={publishMutation.isPending}
                            onClick={handlePublish}
                        >
                            Confirm Publication
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Archive Confirmation Modal */}
            <Modal
                isOpen={isArchiveModalOpen}
                onClose={() => setIsArchiveModalOpen(false)}
                title="Archive Assessment"
            >
                <div className="space-y-4">
                    <p className="text-sm text-foreground-muted">
                        Archiving will permanently decommission this assessment specification. It will no longer be available for student attempts or further modifications. This action is irreversible.
                    </p>
                    <p className="text-xs font-semibold text-danger">
                        Are you sure you want to archive this assessment?
                    </p>
                    <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                        <Button
                            variant="secondary"
                            onClick={() => setIsArchiveModalOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="danger"
                            loading={archiveMutation.isPending}
                            onClick={handleArchive}
                        >
                            Confirm Archive
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Generate Paper Confirmation Modal */}
            <Modal
                isOpen={isGenerateModalOpen}
                onClose={() => setIsGenerateModalOpen(false)}
                title="Generate Assessment Paper"
            >
                <div className="space-y-4">
                    <p className="text-sm text-foreground-muted">
                        Generate a test paper from the current published assessment definition?
                    </p>
                    <div className="p-3 bg-neutral-50 rounded-md border border-neutral-200 text-xs text-foreground-muted">
                        <span className="font-semibold text-neutral-800">
                            Immutable Historical Artifact:
                        </span>{" "}
                        The generated paper will resolve eligible published questions from the Question Bank according to your selection rules and freeze their exact versions, presentation order, and score weights. Future edits in Question Bank will not alter this paper.
                    </div>
                    <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                        <Button
                            variant="secondary"
                            onClick={() => setIsGenerateModalOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="primary"
                            loading={generatePaperMutation.isPending}
                            onClick={handleGeneratePaper}
                        >
                            Generate Paper
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};
