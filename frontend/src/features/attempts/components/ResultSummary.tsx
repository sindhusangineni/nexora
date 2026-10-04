import React from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { AttemptStatusBadge, AttemptResultStatusBadge } from "./AttemptStatusBadge";
import {
    ClockIcon,
    AwardIcon,
    CheckCircleIcon,
    XCircleIcon,
    MinusCircleIcon,
    AlertCircleIcon,
} from "./Icons";
import type { AttemptResult, AttemptStatus, SubmissionReason } from "../types/attempt.types";

interface ResultSummaryProps {
    attemptNumber: number;
    attemptStatus: AttemptStatus;
    result: AttemptResult | null;
    paperTitle?: string;
    submittedAt?: string | null;
    startedAt?: string;
    durationSeconds?: number;
    submissionReason?: SubmissionReason | null;
}

export const ResultSummary: React.FC<ResultSummaryProps> = ({
    attemptNumber,
    attemptStatus,
    result,
    paperTitle,
    submittedAt,
    startedAt,
    durationSeconds,
    submissionReason,
}) => {
    const isPending = result?.status === "PENDING" || attemptStatus === "SUBMITTED";
    const isVoid = result?.status === "VOID" || attemptStatus === "CANCELLED";

    const maxScoreNum = result ? parseFloat(result.maximum_score) : 0;
    const percentageNum = result ? parseFloat(result.percentage) : 0;

    const formatDuration = (secs?: number) => {
        if (!secs) return "—";
        const mins = Math.floor(secs / 60);
        const remainingSecs = secs % 60;
        if (mins === 0) return `${remainingSecs}s`;
        return `${mins}m ${remainingSecs}s`;
    };

    return (
        <Card className="p-6 sm:p-8 space-y-6 shadow-xs border-border bg-surface">
            {/* Header info & badges */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
                <div>
                    <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                            Scorecard Summary
                        </span>
                        <span className="text-foreground-muted text-xs">•</span>
                        <span className="text-xs font-medium text-foreground-muted">
                            Attempt #{attemptNumber}
                        </span>
                    </div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight mt-1">
                        {paperTitle || "Assessment Review & Results"}
                    </h1>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-foreground-muted mt-1.5">
                        {startedAt && (
                            <span>
                                Started: {new Date(startedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
                            </span>
                        )}
                        {submittedAt && (
                            <>
                                <span>•</span>
                                <span>
                                    Submitted: {new Date(submittedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
                                </span>
                            </>
                        )}
                        {durationSeconds !== undefined && durationSeconds > 0 && (
                            <>
                                <span>•</span>
                                <span>Duration: {formatDuration(durationSeconds)}</span>
                            </>
                        )}
                        {submissionReason && (
                            <>
                                <span>•</span>
                                <span className="capitalize">
                                    Reason: {submissionReason.toLowerCase().replace("_", " ")}
                                </span>
                            </>
                        )}
                    </div>
                </div>

                <div className="flex items-center space-x-2 sm:self-start shrink-0">
                    <AttemptStatusBadge status={attemptStatus} />
                    {result && <AttemptResultStatusBadge status={result.status} />}
                </div>
            </div>

            {/* Score Achieved Banner */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2 p-5 bg-linear-to-br from-primary-50/50 via-surface to-surface-muted/30 rounded-xl border border-primary-100 flex flex-col justify-between">
                    <div className="flex items-start justify-between">
                        <div>
                            <span className="text-xs font-bold text-primary-800 uppercase tracking-wider block">
                                Overall Performance
                            </span>
                            {isPending ? (
                                <div className="mt-2 flex items-center space-x-2">
                                    <ClockIcon className="w-5 h-5 text-amber-600 animate-pulse" />
                                    <span className="text-xl font-bold text-amber-900">
                                        Evaluation In Progress
                                    </span>
                                </div>
                            ) : (
                                <div className="mt-2 flex items-baseline space-x-3">
                                    <span className="text-3xl sm:text-4xl font-extrabold text-foreground">
                                        {result?.score || "0.00"}
                                    </span>
                                    <span className="text-sm font-semibold text-foreground-muted">
                                        / {result?.maximum_score || "0.00"} Marks
                                    </span>
                                    <Badge
                                        variant={percentageNum >= 60 ? "success" : percentageNum >= 40 ? "warning" : "danger"}
                                        size="md"
                                        className="ml-2 font-bold"
                                    >
                                        {percentageNum.toFixed(2)}%
                                    </Badge>
                                </div>
                            )}
                        </div>

                        <div className="hidden sm:block p-3 rounded-full bg-primary-100/60 text-primary-700">
                            <AwardIcon className="w-6 h-6" />
                        </div>
                    </div>

                    {/* Progress bar */}
                    {!isPending && !isVoid && maxScoreNum > 0 && (
                        <div className="mt-4 space-y-1.5">
                            <div className="flex justify-between text-[11px] text-foreground-muted">
                                <span>Score Progress</span>
                                <span>{percentageNum.toFixed(1)}% of maximum score</span>
                            </div>
                            <div className="w-full bg-neutral-200 rounded-full h-2 overflow-hidden">
                                <div
                                    className={`h-2 rounded-full transition-all duration-500 ${
                                        percentageNum >= 60
                                            ? "bg-emerald-500"
                                            : percentageNum >= 40
                                            ? "bg-amber-500"
                                            : "bg-red-500"
                                    }`}
                                    style={{ width: `${Math.min(100, Math.max(0, percentageNum))}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Status Callout Card */}
                <div className="p-5 rounded-xl border flex flex-col justify-center bg-surface-muted/30 border-border">
                    {isPending ? (
                        <div className="space-y-2">
                            <div className="flex items-center space-x-1.5 text-amber-700 text-xs font-semibold">
                                <ClockIcon className="w-4 h-4 shrink-0" />
                                <span>Pending Descriptive Review</span>
                            </div>
                            <p className="text-xs text-foreground-muted leading-relaxed">
                                Objective questions are graded. Descriptive questions are being evaluated. This screen will update automatically.
                            </p>
                        </div>
                    ) : isVoid ? (
                        <div className="space-y-2">
                            <div className="flex items-center space-x-1.5 text-red-700 text-xs font-semibold">
                                <AlertCircleIcon className="w-4 h-4 shrink-0" />
                                <span>Attempt Voided / Cancelled</span>
                            </div>
                            <p className="text-xs text-foreground-muted leading-relaxed">
                                This attempt was voided or cancelled by an administrator. Final marks are not recorded.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            <div className="flex items-center space-x-1.5 text-emerald-700 text-xs font-semibold">
                                <CheckCircleIcon className="w-4 h-4 shrink-0" />
                                <span>Finalized Evaluation</span>
                            </div>
                            <p className="text-xs text-foreground-muted leading-relaxed">
                                Full review, answer keys, explanations, and section performance breakdown are unlocked below.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Score Breakdown Stat Pills */}
            {result && (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 text-center">
                    <div className="p-3 bg-surface-muted/40 rounded-lg border border-border">
                        <span className="text-[11px] text-foreground-muted font-medium block">
                            Questions
                        </span>
                        <span className="text-base sm:text-lg font-bold text-foreground mt-0.5 block">
                            {result.total_questions}
                        </span>
                    </div>

                    <div className="p-3 bg-surface-muted/40 rounded-lg border border-border">
                        <span className="text-[11px] text-foreground-muted font-medium block">
                            Attempted
                        </span>
                        <span className="text-base sm:text-lg font-bold text-foreground mt-0.5 block">
                            {result.attempted_questions}
                        </span>
                    </div>

                    <div className="p-3 bg-emerald-50/70 rounded-lg border border-emerald-200/80">
                        <span className="text-[11px] text-emerald-800 font-medium flex items-center justify-center space-x-1">
                            <CheckCircleIcon className="w-3 h-3" />
                            <span>Correct</span>
                        </span>
                        <span className="text-base sm:text-lg font-bold text-emerald-700 mt-0.5 block">
                            {result.correct_questions}
                        </span>
                    </div>

                    <div className="p-3 bg-red-50/70 rounded-lg border border-red-200/80">
                        <span className="text-[11px] text-red-800 font-medium flex items-center justify-center space-x-1">
                            <XCircleIcon className="w-3 h-3" />
                            <span>Incorrect</span>
                        </span>
                        <span className="text-base sm:text-lg font-bold text-red-700 mt-0.5 block">
                            {result.incorrect_questions}
                        </span>
                    </div>

                    <div className="p-3 bg-amber-50/70 rounded-lg border border-amber-200/80">
                        <span className="text-[11px] text-amber-800 font-medium flex items-center justify-center space-x-1">
                            <ClockIcon className="w-3 h-3" />
                            <span>Pending</span>
                        </span>
                        <span className="text-base sm:text-lg font-bold text-amber-700 mt-0.5 block">
                            {result.pending_evaluation_questions}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-100/70 rounded-lg border border-neutral-200">
                        <span className="text-[11px] text-neutral-600 font-medium flex items-center justify-center space-x-1">
                            <MinusCircleIcon className="w-3 h-3" />
                            <span>Unanswered</span>
                        </span>
                        <span className="text-base sm:text-lg font-bold text-neutral-700 mt-0.5 block">
                            {result.unanswered_questions}
                        </span>
                    </div>
                </div>
            )}
        </Card>
    );
};
