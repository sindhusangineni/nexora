import React from "react";
import { Badge } from "@/shared/ui/Badge";
import { Card } from "@/shared/ui/Card";
import { AssessmentStatusBadge, AssessmentTypeBadge } from "./AssessmentStatusBadge";
import type {
    Assessment,
    AssessmentSection,
    ScoreFloorPolicy,
    SelectionRule,
} from "../types/assessment.types";

interface AssessmentReviewProps {
    assessment: Assessment;
    sections: AssessmentSection[];
    rules: SelectionRule[];
    scoreFloorPolicy?: ScoreFloorPolicy;
}

export const AssessmentReview: React.FC<AssessmentReviewProps> = ({
    assessment,
    sections,
    rules,
    scoreFloorPolicy = "UNRESTRICTED",
}) => {
    const durationMinutes = Math.round(assessment.duration_seconds / 60);
    const totalQuestions = rules.reduce((acc, r) => acc + r.question_count, 0);

    // Readiness checklist
    const checks = [
        {
            label: "Assessment Title Defined",
            passed: Boolean(assessment.title?.trim()),
            detail: assessment.title || "Missing title",
        },
        {
            label: "Timing Configuration Valid",
            passed: assessment.duration_seconds > 0,
            detail: `${durationMinutes} minutes (${assessment.duration_seconds}s)`,
        },
        {
            label: "Marking Scheme Valid",
            passed:
                parseFloat(assessment.marks_per_question) > 0 &&
                parseFloat(assessment.penalty_per_question) >= 0,
            detail: `+${assessment.marks_per_question} / -${assessment.penalty_per_question}`,
        },
        {
            label: "Selection Rules Configured",
            passed: rules.length > 0,
            detail: `${rules.length} rule${rules.length === 1 ? "" : "s"} defined`,
        },
        {
            label: "Total Question Count Positive",
            passed: totalQuestions > 0,
            detail: `~${totalQuestions} requested questions`,
        },
    ];

    const isReadyToPublish = checks.every((c) => c.passed);

    // Section breakdown
    const sectionBreakdown = sections.map((sec) => {
        const secRules = rules.filter((r) => r.assessment_section_id === sec.id);
        const secQuestions = secRules.reduce((sum, r) => sum + r.question_count, 0);
        return {
            section: sec,
            rulesCount: secRules.length,
            questionsCount: secQuestions,
        };
    });

    const unassignedRules = rules.filter((r) => !r.assessment_section_id);
    const unassignedQuestions = unassignedRules.reduce(
        (sum, r) => sum + r.question_count,
        0,
    );

    return (
        <div className="space-y-6">
            {/* Overview Card */}
            <Card className="p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-border pb-4">
                    <div>
                        <div className="flex items-center space-x-2">
                            <h3 className="text-lg font-bold text-foreground tracking-tight">
                                {assessment.title}
                            </h3>
                            <AssessmentStatusBadge status={assessment.status} />
                            <AssessmentTypeBadge type={assessment.type} />
                        </div>
                        {assessment.description && (
                            <p className="text-xs text-foreground-muted mt-1 max-w-2xl">
                                {assessment.description}
                            </p>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Duration</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            {durationMinutes} mins
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Marking</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            +{assessment.marks_per_question} / -{assessment.penalty_per_question}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Sections</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            {sections.length}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Requested Questions</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            ~{totalQuestions} ({rules.length} rules)
                        </span>
                    </div>
                </div>

                <div className="text-xs text-foreground-muted">
                    <span className="font-semibold text-neutral-700">Scoring Policy: </span>
                    <span className="font-medium text-neutral-900">
                        {scoreFloorPolicy === "ZERO_FLOOR_TOTAL"
                            ? "Zero Floor — Total (cannot fall below 0.00 total)"
                            : scoreFloorPolicy === "ZERO_FLOOR_SECTION"
                            ? "Zero Floor — Section (cannot fall below 0.00 per section)"
                            : "Unrestricted (negative marks accumulate freely)"}
                    </span>
                </div>
            </Card>

            {/* Sections & Rules Breakdown */}
            <Card className="p-6 space-y-4">
                <h4 className="text-sm font-semibold text-foreground tracking-tight">
                    Structure Breakdown
                </h4>

                {sections.length > 0 ? (
                    <div className="space-y-3">
                        {sectionBreakdown.map(({ section, rulesCount, questionsCount }) => (
                            <div
                                key={section.id}
                                className="p-3.5 bg-surface border border-border rounded-lg flex items-center justify-between text-xs"
                            >
                                <div>
                                    <span className="font-semibold text-neutral-900">
                                        Section {section.position + 1}: {section.title}
                                    </span>
                                    {section.description && (
                                        <p className="text-foreground-muted text-[11px] mt-0.5">
                                            {section.description}
                                        </p>
                                    )}
                                </div>
                                <div className="flex items-center space-x-2">
                                    <Badge variant="default" size="sm">
                                        {rulesCount} {rulesCount === 1 ? "rule" : "rules"}
                                    </Badge>
                                    <Badge variant="info" size="sm">
                                        ~{questionsCount} questions
                                    </Badge>
                                </div>
                            </div>
                        ))}

                        {unassignedRules.length > 0 && (
                            <div className="p-3.5 bg-neutral-50/80 border border-neutral-200 rounded-lg flex items-center justify-between text-xs">
                                <div>
                                    <span className="font-medium text-neutral-800">
                                        Assessment Level (No Specific Section)
                                    </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <Badge variant="default" size="sm">
                                        {unassignedRules.length} rules
                                    </Badge>
                                    <Badge variant="info" size="sm">
                                        ~{unassignedQuestions} questions
                                    </Badge>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="p-4 bg-neutral-50 border border-neutral-200 rounded-lg text-xs text-foreground-muted flex justify-between items-center">
                        <span>Assessment Level (No sections configured)</span>
                        <div className="flex items-center space-x-2">
                            <Badge variant="default" size="sm">
                                {rules.length} rules
                            </Badge>
                            <Badge variant="info" size="sm">
                                ~{totalQuestions} questions
                            </Badge>
                        </div>
                    </div>
                )}
            </Card>

            {/* Publication Readiness Checklist */}
            <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-foreground tracking-tight">
                        Publication Readiness Checklist
                    </h4>
                    <Badge variant={isReadyToPublish ? "success" : "warning"} size="sm">
                        {isReadyToPublish ? "Ready to Publish" : "Incomplete Requirements"}
                    </Badge>
                </div>

                <div className="space-y-2">
                    {checks.map((check, idx) => (
                        <div
                            key={idx}
                            className={`flex items-center justify-between p-2.5 rounded-md border text-xs ${
                                check.passed
                                    ? "bg-success-surface/40 border-success/20 text-neutral-900"
                                    : "bg-warning-surface/40 border-warning/20 text-neutral-900"
                            }`}
                        >
                            <div className="flex items-center space-x-2">
                                <span
                                    className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                        check.passed
                                            ? "bg-success text-white"
                                            : "bg-warning text-neutral-900"
                                    }`}
                                >
                                    {check.passed ? "✓" : "!"}
                                </span>
                                <span className="font-medium">{check.label}</span>
                            </div>
                            <span className="text-foreground-muted font-mono">{check.detail}</span>
                        </div>
                    ))}
                </div>
            </Card>
        </div>
    );
};
