import React, { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import {
    AssessmentLifecycleActions,
    AssessmentReview,
    AssessmentStatusBadge,
    AssessmentTypeBadge,
    useAssessment,
    useAssessmentSections,
    useSelectionRules,
    type AssessmentStatus,
    type AssessmentType,
    type ScoreFloorPolicy,
} from "@/features/assessment";

export const AdminAssessmentDetailPage: React.FC = () => {
    const { assessmentId } = useParams<{ assessmentId: string }>();
    const navigate = useNavigate();

    const {
        data: assessment,
        isLoading: isLoadingAssessment,
        error: assessmentError,
    } = useAssessment(assessmentId || "");

    const { data: sections = [], isLoading: isLoadingSections } =
        useAssessmentSections(assessmentId || "");

    const { data: rules = [], isLoading: isLoadingRules } =
        useSelectionRules(assessmentId || "");

    const [scoreFloorPolicy] = useState<ScoreFloorPolicy>("UNRESTRICTED");

    if (isLoadingAssessment || isLoadingSections || isLoadingRules) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-10 w-3/4" />
                <div className="grid grid-cols-4 gap-4">
                    <Skeleton className="h-20" />
                    <Skeleton className="h-20" />
                    <Skeleton className="h-20" />
                    <Skeleton className="h-20" />
                </div>
            </div>
        );
    }

    if (assessmentError || !assessment) {
        return (
            <div className="p-6 bg-danger-surface border border-danger/20 rounded-lg text-danger space-y-3">
                <h3 className="font-semibold text-base">Assessment Not Found</h3>
                <p className="text-sm">
                    The requested assessment could not be loaded. It may have been deleted or does not exist.
                </p>
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate("/admin/assessments")}
                >
                    Back to Assessments
                </Button>
            </div>
        );
    }

    const isDraft = assessment.status === "DRAFT";

    return (
        <div className="space-y-6">
            {/* Breadcrumb */}
            <div className="flex items-center space-x-2 text-xs text-foreground-muted">
                <Link
                    to="/admin/assessments"
                    className="hover:text-foreground transition-colors"
                >
                    Assessments
                </Link>
                <span>/</span>
                <span className="text-foreground font-medium truncate max-w-xs">
                    {assessment.title}
                </span>
            </div>

            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
                <div className="space-y-2">
                    <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                        <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                            {assessment.title}
                        </h1>
                        <AssessmentStatusBadge
                            status={assessment.status as AssessmentStatus}
                        />
                        <AssessmentTypeBadge
                            type={assessment.type as AssessmentType}
                        />
                    </div>
                    {assessment.description && (
                        <p className="text-sm text-foreground-muted max-w-3xl leading-relaxed">
                            {assessment.description}
                        </p>
                    )}
                </div>

                <div className="flex items-center space-x-3 flex-shrink-0">
                    {isDraft && (
                        <Button
                            variant="secondary"
                            onClick={() =>
                                navigate(`/admin/assessments/${assessment.id}/edit`)
                            }
                        >
                            Edit Builder
                        </Button>
                    )}
                </div>
            </div>

            {/* Lifecycle Action Bar */}
            <div className="p-4 bg-surface border border-border rounded-lg shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h3 className="text-sm font-semibold text-foreground">
                            Assessment Actions
                        </h3>
                        <p className="text-xs text-foreground-muted">
                            Manage assessment lifecycle and paper generation.
                        </p>
                    </div>

                    <AssessmentLifecycleActions
                        assessment={assessment}
                        rules={rules}
                        onPaperGenerated={(paperId) =>
                            navigate(
                                `/admin/assessments/${assessment.id}/paper?paperId=${paperId}`,
                            )
                        }
                    />
                </div>
            </div>

            {/* Full Review & Structure Summary */}
            <AssessmentReview
                assessment={assessment}
                sections={sections}
                rules={rules}
                scoreFloorPolicy={scoreFloorPolicy}
            />
        </div>
    );
};
