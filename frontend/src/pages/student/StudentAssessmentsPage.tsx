import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Button } from "@/shared/ui/Button";
import {
    AssessmentTypeBadge,
    useAssessments,
    assessmentApi,
    type AssessmentType,
    type Assessment,
} from "@/features/assessment";
import { useStartAttempt } from "@/features/attempts";

export const StudentAssessmentsPage: React.FC = () => {
    const navigate = useNavigate();
    const { data: assessments = [], isLoading, error } = useAssessments();
    const startAttemptMutation = useStartAttempt();

    const [startingAssessmentId, setStartingAssessmentId] = useState<string | null>(null);
    const [startError, setStartError] = useState<string | null>(null);

    // Students only receive published assessments from the backend
    const publishedAssessments = assessments.filter(
        (a) => a.status === "PUBLISHED",
    );

    const handleStartAssessment = async (assessment: Assessment) => {
        setStartingAssessmentId(assessment.id);
        setStartError(null);

        try {
            // Retrieve or generate paper snapshot for this published assessment
            const paper = await assessmentApi.generatePaper(assessment.id);

            // Start or resume active attempt session idempotently
            const attempt = await startAttemptMutation.mutateAsync({
                assessment_paper_id: paper.id,
            });

            navigate(`/student/attempts/${attempt.id}`);
        } catch (err: unknown) {
            const msg =
                err instanceof Error
                    ? err.message
                    : "Unable to start assessment session. Please try again.";
            setStartError(msg);
            setStartingAssessmentId(null);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                        Available Assessments
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Explore available practice tests, revision sets, and full-length UPSC mock examinations.
                    </p>
                </div>

                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate("/student/attempts")}
                >
                    View My Attempts
                </Button>
            </div>

            {startError && (
                <div className="p-4 bg-danger-surface border border-danger/20 rounded-md text-xs text-danger">
                    {startError}
                </div>
            )}

            {error && (
                <div className="p-4 bg-danger-surface border border-danger/20 rounded-md text-sm text-danger">
                    Failed to load assessments. Please try again later.
                </div>
            )}

            {isLoading && (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div
                            key={i}
                            className="p-5 bg-surface border border-border rounded-lg space-y-3"
                        >
                            <Skeleton className="h-5 w-1/3" />
                            <Skeleton className="h-4 w-2/3" />
                            <Skeleton className="h-6 w-24" />
                        </div>
                    ))}
                </div>
            )}

            {!isLoading && publishedAssessments.length === 0 && (
                <EmptyState
                    title="No Assessments Available"
                    description="There are currently no published assessments available. Please check back later."
                />
            )}

            {!isLoading && publishedAssessments.length > 0 && (
                <div className="space-y-4">
                    {publishedAssessments.map((assessment) => {
                        const durationMinutes = Math.round(
                            assessment.duration_seconds / 60,
                        );
                        const isStarting = startingAssessmentId === assessment.id;

                        return (
                            <div
                                key={assessment.id}
                                className="p-5 bg-surface border border-border rounded-lg shadow-2xs hover:border-neutral-300 transition-colors"
                            >
                                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                                    <div className="space-y-2 flex-1">
                                        <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                                            <h3 className="text-base font-semibold text-foreground">
                                                {assessment.title}
                                            </h3>
                                            <AssessmentTypeBadge
                                                type={assessment.type as AssessmentType}
                                            />
                                        </div>

                                        {assessment.description && (
                                            <p className="text-xs text-foreground-muted leading-relaxed max-w-2xl">
                                                {assessment.description}
                                            </p>
                                        )}

                                        <div className="flex items-center space-x-4 text-xs text-foreground-muted flex-wrap gap-y-1 pt-1">
                                            <span>
                                                Duration:{" "}
                                                <strong className="text-neutral-800">
                                                    {durationMinutes} minutes
                                                </strong>
                                            </span>
                                            <span>•</span>
                                            <span>
                                                Marking:{" "}
                                                <strong className="text-neutral-800">
                                                    +{assessment.marks_per_question} / -
                                                    {assessment.penalty_per_question}
                                                </strong>
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex flex-col items-start sm:items-end justify-between self-stretch sm:self-auto gap-2">
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            onClick={() => handleStartAssessment(assessment)}
                                            disabled={isStarting}
                                            loading={isStarting}
                                        >
                                            {isStarting ? "Starting..." : "Start Assessment"}
                                        </Button>
                                        <span className="text-[11px] text-foreground-muted">
                                            Attempts will be enabled in Phase 3D
                                        </span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};
