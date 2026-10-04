import React from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { ClockIcon, HelpCircleIcon, AwardIcon, AlertCircleIcon } from "./Icons";
import type { Assessment } from "@/features/assessment/types/assessment.types";

interface AttemptStartCardProps {
    assessment: Assessment;
    paperId?: string;
    questionCount?: number;
    onStart: () => void;
    isLoading?: boolean;
    disabled?: boolean;
    className?: string;
}

export const AttemptStartCard: React.FC<AttemptStartCardProps> = ({
    assessment,
    questionCount,
    onStart,
    isLoading = false,
    disabled = false,
    className = "",
}) => {
    const durationMinutes = Math.round(assessment.duration_seconds / 60);

    return (
        <Card className={`p-6 space-y-6 ${className}`}>
            <div>
                <span className="text-xs font-semibold text-primary uppercase tracking-wider block">
                    Assessment Overview
                </span>
                <h2 className="text-xl font-bold text-foreground tracking-tight mt-1">
                    {assessment.title}
                </h2>
                {assessment.description && (
                    <p className="text-sm text-foreground-muted mt-2 leading-relaxed">
                        {assessment.description}
                    </p>
                )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5 text-xs">
                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                    <div className="flex items-center space-x-1.5 text-foreground-muted mb-1">
                        <ClockIcon className="w-3.5 h-3.5 text-neutral-500" />
                        <span className="font-medium">Duration</span>
                    </div>
                    <span className="text-sm font-bold text-neutral-900 block">
                        {durationMinutes} minutes
                    </span>
                </div>

                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                    <div className="flex items-center space-x-1.5 text-foreground-muted mb-1">
                        <HelpCircleIcon className="w-3.5 h-3.5 text-neutral-500" />
                        <span className="font-medium">Questions</span>
                    </div>
                    <span className="text-sm font-bold text-neutral-900 block">
                        {questionCount !== undefined ? `${questionCount} Questions` : "As per paper"}
                    </span>
                </div>

                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200 col-span-2 sm:col-span-1">
                    <div className="flex items-center space-x-1.5 text-foreground-muted mb-1">
                        <AwardIcon className="w-3.5 h-3.5 text-neutral-500" />
                        <span className="font-medium">Marking</span>
                    </div>
                    <span className="text-sm font-bold text-neutral-900 block">
                        +{assessment.marks_per_question} / -{assessment.penalty_per_question}
                    </span>
                </div>
            </div>

            <div className="p-3.5 bg-neutral-50 border border-neutral-200 rounded-lg flex items-start space-x-2.5 text-xs text-foreground-muted">
                <AlertCircleIcon className="w-4 h-4 text-neutral-600 shrink-0 mt-0.5" />
                <p>
                    Once started, your timed session will begin. You can navigate between questions and change answers freely until you submit or time expires.
                </p>
            </div>

            <div className="pt-2 flex justify-end">
                <Button
                    type="button"
                    variant="primary"
                    size="md"
                    onClick={onStart}
                    disabled={disabled || isLoading}
                    className="w-full sm:w-auto"
                >
                    {isLoading ? "Starting Session..." : "Start Assessment Now"}
                </Button>
            </div>
        </Card>
    );
};
