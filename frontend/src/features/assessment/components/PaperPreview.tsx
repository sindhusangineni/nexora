import React from "react";
import { Badge } from "@/shared/ui/Badge";
import { Card } from "@/shared/ui/Card";
import type {
    Assessment,
    AssessmentPaper,
    AssessmentSection,
} from "../types/assessment.types";

interface PaperPreviewProps {
    paper: AssessmentPaper;
    assessment?: Assessment;
    sections?: AssessmentSection[];
}

export const PaperPreview: React.FC<PaperPreviewProps> = ({
    paper,
    assessment,
    sections = [],
}) => {
    const durationMinutes = Math.round(paper.duration_seconds / 60);

    // Group items by section or display in presentation order
    const sortedItems = [...paper.items].sort(
        (a, b) => a.presentation_order - b.presentation_order,
    );

    const getSectionTitle = (sectionId: string | null) => {
        if (!sectionId) return null;
        const found = sections.find((s) => s.id === sectionId);
        return found ? found.title : null;
    };

    return (
        <div className="space-y-6">
            {/* Immutability Banner */}
            <div className="p-4 bg-neutral-900 text-white rounded-lg shadow-sm">
                <div className="flex items-start space-x-3">
                    <span className="p-1 bg-neutral-800 rounded text-neutral-300 text-xs font-mono uppercase">
                        Snapshot
                    </span>
                    <div className="space-y-1">
                        <h4 className="text-sm font-semibold tracking-tight">
                            Immutable Test Paper Artifact
                        </h4>
                        <p className="text-xs text-neutral-400 leading-relaxed">
                            This paper is an immutable snapshot. Changes to the assessment definition or Question Bank do not modify this generated paper. Pinned question versions and scoring allocations are permanently fixed.
                        </p>
                    </div>
                </div>
            </div>

            {/* Paper Header / Metadata Card */}
            <Card className="p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-border pb-4">
                    <div>
                        <span className="text-xs text-foreground-muted font-mono uppercase">
                            Assessment Paper #{paper.id.slice(0, 8)}
                        </span>
                        <h2 className="text-xl font-bold text-foreground tracking-tight mt-0.5">
                            {assessment ? assessment.title : "Generated Assessment Paper"}
                        </h2>
                    </div>
                    <div className="flex items-center space-x-2">
                        <Badge variant="success" size="sm">
                            {paper.status}
                        </Badge>
                        <Badge variant="default" size="sm">
                            {paper.items.length} Questions
                        </Badge>
                    </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Duration</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            {durationMinutes} minutes
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Allocated Marks</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            +{paper.marks_per_question} / -{paper.penalty_per_question}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Generated At</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            {new Date(paper.created_at).toLocaleDateString()}
                        </span>
                    </div>

                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-foreground-muted block font-medium">Total Maximum Score</span>
                        <span className="text-base font-semibold text-neutral-900 mt-0.5 block">
                            {(
                                paper.items.length * parseFloat(paper.marks_per_question)
                            ).toFixed(2)}
                        </span>
                    </div>
                </div>

                <div className="text-xs text-foreground-muted font-mono space-y-0.5">
                    <div>Paper UUID: {paper.id}</div>
                    <div>Assessment UUID: {paper.assessment_id}</div>
                </div>
            </Card>

            {/* Questions Sequence Card */}
            <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                    <h3 className="text-base font-semibold text-foreground tracking-tight">
                        Question Presentation Sequence
                    </h3>
                    <span className="text-xs text-foreground-muted">
                        Ordered 1 to {sortedItems.length}
                    </span>
                </div>

                {sortedItems.length === 0 ? (
                    <div className="py-8 text-center text-xs text-foreground-muted">
                        No questions in this paper artifact.
                    </div>
                ) : (
                    <div className="space-y-3">
                        {sortedItems.map((item) => {
                            const sectionTitle = getSectionTitle(item.assessment_section_id);
                            return (
                                <div
                                    key={item.id}
                                    className="p-4 bg-surface border border-border rounded-lg shadow-2xs space-y-2"
                                >
                                    <div className="flex items-center justify-between flex-wrap gap-2">
                                        <div className="flex items-center space-x-2">
                                            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-neutral-900 text-white text-xs font-semibold">
                                                {item.presentation_order}
                                            </span>
                                            {sectionTitle && (
                                                <Badge variant="default" size="sm">
                                                    Section: {sectionTitle}
                                                </Badge>
                                            )}
                                        </div>
                                        <div className="flex items-center space-x-2 text-xs">
                                            <Badge variant="success" size="sm">
                                                +{item.allocated_marks}
                                            </Badge>
                                            <Badge variant="danger" size="sm">
                                                -{item.allocated_penalty}
                                            </Badge>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-foreground-muted font-mono bg-neutral-50 p-2.5 rounded-md border border-neutral-200">
                                        <div>
                                            <span className="text-neutral-500 font-sans">Question ID:</span>{" "}
                                            <span className="text-neutral-900">{item.question_id}</span>
                                        </div>
                                        <div>
                                            <span className="text-neutral-500 font-sans">Pinned Version:</span>{" "}
                                            <span className="text-neutral-900">{item.question_version_id}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </Card>
        </div>
    );
};
