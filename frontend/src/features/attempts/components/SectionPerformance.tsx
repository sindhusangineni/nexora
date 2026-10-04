import React from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import type { AttemptSectionResult } from "../types/attempt.types";

interface SectionPerformanceProps {
    sectionResults: AttemptSectionResult[];
}

export const SectionPerformance: React.FC<SectionPerformanceProps> = ({
    sectionResults,
}) => {
    if (!sectionResults || sectionResults.length === 0) {
        return null;
    }

    return (
        <Card className="p-6 space-y-4 border-border bg-surface shadow-xs">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-base font-bold text-foreground tracking-tight">
                        Section Performance Breakdown
                    </h2>
                    <p className="text-xs text-foreground-muted mt-0.5">
                        Performance analytics across test sections and subject domains.
                    </p>
                </div>
                <span className="text-xs text-foreground-muted font-medium">
                    {sectionResults.length} {sectionResults.length === 1 ? "Section" : "Sections"}
                </span>
            </div>

            <div className="space-y-3 pt-2">
                {sectionResults.map((sec, idx) => {
                    const score = parseFloat(sec.score);
                    const maxScore = parseFloat(sec.maximum_score);
                    const percentage =
                        sec.percentage !== undefined
                            ? parseFloat(sec.percentage)
                            : maxScore > 0
                            ? Math.round((score / maxScore) * 10000) / 100
                            : 0;

                    const title = sec.section_name || sec.section_title_snapshot || `Section ${idx + 1}`;

                    return (
                        <div
                            key={sec.id || idx}
                            className="p-4 bg-surface-muted/30 border border-border rounded-xl space-y-3 hover:border-primary-200 transition-colors"
                        >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                <div>
                                    <div className="flex items-center space-x-2">
                                        <span className="font-semibold text-foreground text-sm">
                                            {title}
                                        </span>
                                        <Badge
                                            variant={
                                                percentage >= 60
                                                    ? "success"
                                                    : percentage >= 40
                                                    ? "warning"
                                                    : "default"
                                            }
                                            size="sm"
                                        >
                                            {percentage.toFixed(1)}%
                                        </Badge>
                                    </div>
                                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-foreground-muted mt-1">
                                        <span>Attempted: {sec.attempted_questions}</span>
                                        <span>•</span>
                                        <span className="text-emerald-700 font-medium">
                                            {sec.correct_questions} Correct
                                        </span>
                                        <span>•</span>
                                        <span className="text-red-700 font-medium">
                                            {sec.incorrect_questions} Incorrect
                                        </span>
                                        {sec.pending_evaluation_questions > 0 && (
                                            <>
                                                <span>•</span>
                                                <span className="text-amber-700 font-medium">
                                                    {sec.pending_evaluation_questions} Pending
                                                </span>
                                            </>
                                        )}
                                        {sec.unanswered_questions > 0 && (
                                            <>
                                                <span>•</span>
                                                <span>{sec.unanswered_questions} Unanswered</span>
                                            </>
                                        )}
                                    </div>
                                </div>

                                <div className="text-left sm:text-right">
                                    <span className="text-xs text-foreground-muted block font-medium">
                                        Section Score
                                    </span>
                                    <span className="text-lg font-bold text-foreground block">
                                        {sec.score}{" "}
                                        <span className="text-xs text-foreground-muted font-normal">
                                            / {sec.maximum_score}
                                        </span>
                                    </span>
                                </div>
                            </div>

                            {/* Section progress bar */}
                            {maxScore > 0 && (
                                <div className="w-full bg-neutral-200 rounded-full h-1.5 overflow-hidden">
                                    <div
                                        className={`h-1.5 rounded-full transition-all duration-300 ${
                                            percentage >= 60
                                                ? "bg-emerald-500"
                                                : percentage >= 40
                                                ? "bg-amber-500"
                                                : "bg-red-500"
                                        }`}
                                        style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
                                    />
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </Card>
    );
};
