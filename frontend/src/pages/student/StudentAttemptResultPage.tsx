import React from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
    useAttemptReview,
    useAttemptPaper,
    useAttemptAssessment,
    ResultSummary,
    SectionPerformance,
    QuestionReviewList,
} from "@/features/attempts";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import { AlertCircleIcon, ArrowLeftIcon } from "@/features/attempts/components/Icons";

export const StudentAttemptResultPage: React.FC = () => {
    const { attemptId } = useParams<{ attemptId: string }>();
    const navigate = useNavigate();

    const {
        data: review,
        isLoading,
        isError,
        error,
        refetch,
    } = useAttemptReview(attemptId || "", { enabled: !!attemptId });

    const { data: paper } = useAttemptPaper(review?.assessment_paper_id);
    const { data: assessment } = useAttemptAssessment(paper?.assessment_id);

    if (isLoading) {
        return (
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
                <div className="flex items-center space-x-2">
                    <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-72 w-full rounded-2xl" />
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <Skeleton className="h-28 w-full rounded-xl" />
                    <Skeleton className="h-28 w-full rounded-xl" />
                    <Skeleton className="h-28 w-full rounded-xl" />
                </div>
                <Skeleton className="h-96 w-full rounded-2xl" />
            </div>
        );
    }

    if (isError || !review) {
        return (
            <div className="max-w-md mx-auto px-4 py-16 text-center">
                <Card className="p-6 space-y-4 border-border bg-surface shadow-xs">
                    <AlertCircleIcon className="w-10 h-10 text-red-500 mx-auto" />
                    <h2 className="text-base font-bold text-foreground">Attempt Review Not Found</h2>
                    <p className="text-xs text-foreground-muted leading-relaxed">
                        {error instanceof Error
                            ? error.message
                            : "Unable to find or load the requested assessment review."}
                    </p>
                    <div className="flex items-center justify-center space-x-3 pt-2">
                        <Button size="sm" variant="secondary" onClick={() => refetch()}>
                            Retry
                        </Button>
                        <Button size="sm" variant="primary" onClick={() => navigate("/student/attempts")}>
                            My Attempts
                        </Button>
                    </div>
                </Card>
            </div>
        );
    }

    const isFinalized = review.result_status === "FINAL";

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
            {/* Top Navigation & Breadcrumbs */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                <div className="flex items-center space-x-2 text-xs">
                    <Link
                        to="/student/attempts"
                        className="inline-flex items-center space-x-1.5 text-foreground-muted hover:text-foreground font-medium transition-colors"
                    >
                        <ArrowLeftIcon className="w-3.5 h-3.5" />
                        <span>My Attempts</span>
                    </Link>
                    <span className="text-border">/</span>
                    <span className="text-foreground font-semibold">
                        Attempt #{review.attempt_number} Result & Review
                    </span>
                </div>

                <div className="flex items-center space-x-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => navigate("/student/attempts")}
                    >
                        All Attempts
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => navigate("/student/assessments")}
                    >
                        Browse Assessments
                    </Button>
                </div>
            </div>

            {/* 1. Scorecard Hero Summary */}
            <ResultSummary
                attemptNumber={review.attempt_number}
                attemptStatus={review.status}
                result={review.result}
                paperTitle={assessment?.title}
                startedAt={review.started_at}
                submittedAt={review.submitted_at}
                durationSeconds={review.duration_seconds}
                submissionReason={review.submission_reason}
            />

            {/* 2. Section Performance Breakdown */}
            {review.result?.section_results && review.result.section_results.length > 0 && (
                <SectionPerformance sectionResults={review.result.section_results} />
            )}

            {/* 3. Question-by-Question Review with solutions & explanations */}
            {review.items && review.items.length > 0 && (
                <QuestionReviewList
                    items={review.items}
                    isFinalized={isFinalized}
                />
            )}

            {/* Bottom Actions */}
            <div className="flex items-center justify-between border-t border-border pt-6">
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate("/student/attempts")}
                >
                    View All Attempts
                </Button>

                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate("/student/assessments")}
                >
                    Browse Available Tests
                </Button>
            </div>
        </div>
    );
};
