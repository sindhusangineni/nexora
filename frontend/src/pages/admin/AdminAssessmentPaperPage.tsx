import React from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import {
    PaperPreview,
    useAssessment,
    useAssessmentPaper,
    useAssessmentSections,
    useGeneratePaper,
} from "@/features/assessment";

export const AdminAssessmentPaperPage: React.FC = () => {
    const { assessmentId } = useParams<{ assessmentId: string }>();
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();

    const paperId = searchParams.get("paperId");

    const {
        data: assessment,
        isLoading: isLoadingAssessment,
        error: assessmentError,
    } = useAssessment(assessmentId || "");

    const { data: sections = [] } = useAssessmentSections(assessmentId || "");

    const {
        data: paper,
        isLoading: isLoadingPaper,
        error: paperError,
    } = useAssessmentPaper(paperId || "");

    const generatePaperMutation = useGeneratePaper(assessmentId || "");

    const handleGenerate = async () => {
        try {
            const newPaper = await generatePaperMutation.mutateAsync();
            setSearchParams({ paperId: newPaper.id });
        } catch {
            // Mutation error will be displayed
        }
    };

    if (isLoadingAssessment || (paperId && isLoadingPaper)) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-10 w-3/4" />
                <Skeleton className="h-64" />
            </div>
        );
    }

    if (assessmentError || !assessment) {
        return (
            <div className="p-6 bg-danger-surface border border-danger/20 rounded-lg text-danger space-y-3">
                <h3 className="font-semibold text-base">Assessment Not Found</h3>
                <p className="text-sm">The assessment could not be loaded.</p>
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
                <Link
                    to={`/admin/assessments/${assessment.id}`}
                    className="hover:text-foreground transition-colors truncate max-w-xs"
                >
                    {assessment.title}
                </Link>
                <span>/</span>
                <span className="text-foreground font-medium">Paper Artifact</span>
            </div>

            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                        Assessment Paper
                    </h1>
                    <p className="text-xs text-foreground-muted mt-1">
                        Generated immutable test paper artifact for {assessment.title}
                    </p>
                </div>

                <div className="flex items-center space-x-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => navigate(`/admin/assessments/${assessment.id}`)}
                    >
                        Back to Assessment
                    </Button>

                    {assessment.status === "PUBLISHED" && (
                        <Button
                            variant="primary"
                            size="sm"
                            loading={generatePaperMutation.isPending}
                            onClick={handleGenerate}
                        >
                            Generate New Paper
                        </Button>
                    )}
                </div>
            </div>

            {generatePaperMutation.isError && (
                <div className="p-4 bg-danger-surface border border-danger/20 rounded-md text-xs text-danger">
                    Failed to generate paper:{" "}
                    {generatePaperMutation.error instanceof Error
                        ? generatePaperMutation.error.message
                        : "Ensure sufficient eligible questions exist in the Question Bank matching selection rules."}
                </div>
            )}

            {paperError && (
                <div className="p-4 bg-danger-surface border border-danger/20 rounded-md text-xs text-danger">
                    Failed to load paper artifact.
                </div>
            )}

            {paper ? (
                <PaperPreview
                    paper={paper}
                    assessment={assessment}
                    sections={sections}
                />
            ) : (
                <div className="p-12 text-center bg-surface border border-border rounded-lg shadow-2xs space-y-4">
                    <div className="max-w-md mx-auto space-y-2">
                        <h3 className="text-base font-semibold text-foreground">
                            No Paper Artifact Selected
                        </h3>
                        <p className="text-xs text-foreground-muted leading-relaxed">
                            {assessment.status === "PUBLISHED"
                                ? "This published assessment is ready to generate an immutable test paper. Click below to execute paper generation."
                                : "Papers can only be generated from PUBLISHED assessments. This assessment is currently in " +
                                  assessment.status +
                                  " status."}
                        </p>
                    </div>

                    {assessment.status === "PUBLISHED" && (
                        <Button
                            variant="primary"
                            loading={generatePaperMutation.isPending}
                            onClick={handleGenerate}
                        >
                            Generate Assessment Paper Now
                        </Button>
                    )}
                </div>
            )}
        </div>
    );
};
