import React, { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Modal } from "@/shared/ui/Modal";
import { EmptyState } from "@/shared/ui/EmptyState";
import { SelectionRuleEditor } from "./SelectionRuleEditor";
import { useDeleteSelectionRule } from "../hooks/useAssessment";
import type {
    AssessmentSection,
    SelectionRule,
} from "../types/assessment.types";

interface SelectionRuleListProps {
    assessmentId: string;
    rules: SelectionRule[];
    sections: AssessmentSection[];
    isDraft: boolean;
}

export const SelectionRuleList: React.FC<SelectionRuleListProps> = ({
    assessmentId,
    rules,
    sections,
    isDraft,
}) => {
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [deleteRuleId, setDeleteRuleId] = useState<string | null>(null);

    const deleteRuleMutation = useDeleteSelectionRule(assessmentId);

    const sortedRules = [...rules].sort((a, b) => a.position - b.position);
    const totalQuestions = rules.reduce((sum, r) => sum + r.question_count, 0);

    const handleDelete = async () => {
        if (!deleteRuleId) return;
        try {
            await deleteRuleMutation.mutateAsync(deleteRuleId);
            setDeleteRuleId(null);
        } catch {
            // Error handled by mutation
        }
    };

    const getSectionTitle = (sectionId: string | null) => {
        if (!sectionId) return "Assessment Level";
        const found = sections.find((s) => s.id === sectionId);
        return found ? found.title : "Section";
    };

    return (
        <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-semibold text-foreground tracking-tight">
                            Selection Rules
                        </h3>
                        <Badge variant="default" size="sm">
                            {rules.length} {rules.length === 1 ? "rule" : "rules"}
                        </Badge>
                        <Badge variant="info" size="sm">
                            ~{totalQuestions} total questions
                        </Badge>
                    </div>
                    <p className="text-xs text-foreground-muted mt-0.5">
                        Define criteria that dynamically select published questions into the generated assessment paper.
                    </p>
                </div>
                {isDraft && (
                    <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setIsAddOpen(true)}
                        aria-label="Add Selection Rule"
                    >
                        + Add Rule
                    </Button>
                )}
            </div>

            {sortedRules.length === 0 ? (
                <EmptyState
                    title="No Selection Rules Configured"
                    description={
                        isDraft
                            ? "At least one selection rule is required before this assessment can be published and generated into a test paper."
                            : "No selection rules configured."
                    }
                    action={
                        isDraft ? (
                            <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setIsAddOpen(true)}
                            >
                                Add First Selection Rule
                            </Button>
                        ) : undefined
                    }
                />
            ) : (
                <div className="space-y-3">
                    {sortedRules.map((rule, idx) => (
                        <div
                            key={rule.id}
                            className="p-4 bg-surface border border-border rounded-lg shadow-2xs hover:border-neutral-300 transition-colors"
                        >
                            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                                <div className="space-y-2">
                                    <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                                        <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-sm bg-neutral-100 text-neutral-800 text-xs font-semibold">
                                            Rule #{idx + 1} (Pos {rule.position})
                                        </span>
                                        <Badge variant="default" size="sm">
                                            {rule.scope_type}
                                        </Badge>
                                        {rule.question_type && (
                                            <Badge variant="info" size="sm">
                                                {rule.question_type}
                                            </Badge>
                                        )}
                                        {rule.difficulty && (
                                            <Badge
                                                variant={
                                                    rule.difficulty === "EASY"
                                                        ? "success"
                                                        : rule.difficulty === "HARD"
                                                        ? "danger"
                                                        : "warning"
                                                }
                                                size="sm"
                                            >
                                                {rule.difficulty}
                                            </Badge>
                                        )}
                                        <span className="text-xs font-semibold text-primary">
                                            {rule.question_count} questions
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-xs text-foreground-muted">
                                        <div>
                                            <span className="font-medium text-neutral-600">
                                                Scope Entity UUID:
                                            </span>{" "}
                                            <span className="font-mono text-neutral-800">
                                                {rule.scope_id}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-medium text-neutral-600">
                                                Assigned Section:
                                            </span>{" "}
                                            <span className="text-neutral-800">
                                                {getSectionTitle(rule.assessment_section_id)}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {isDraft && (
                                    <div className="flex sm:flex-col items-end">
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            onClick={() => setDeleteRuleId(rule.id)}
                                            aria-label={`Delete Rule ${idx + 1}`}
                                        >
                                            Delete
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    <div className="p-3 bg-neutral-50 border border-neutral-200 rounded-md text-xs text-foreground-muted flex items-start space-x-2">
                        <span className="font-semibold text-neutral-700">Note:</span>
                        <span>
                            Overlapping rules may resolve to fewer questions because each question can appear only once in a generated paper. Deduplication happens automatically during paper generation.
                        </span>
                    </div>
                </div>
            )}

            {/* Selection Rule Editor Modal */}
            <SelectionRuleEditor
                assessmentId={assessmentId}
                sections={sections}
                existingRulesCount={rules.length}
                isOpen={isAddOpen}
                onClose={() => setIsAddOpen(false)}
            />

            {/* Delete Rule Confirmation Modal */}
            <Modal
                isOpen={Boolean(deleteRuleId)}
                onClose={() => setDeleteRuleId(null)}
                title="Delete Selection Rule"
            >
                <div className="space-y-4">
                    <p className="text-sm text-foreground-muted">
                        Are you sure you want to delete this selection rule? The assessment paper will no longer select questions matching these criteria.
                    </p>
                    <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                        <Button
                            variant="secondary"
                            onClick={() => setDeleteRuleId(null)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="danger"
                            loading={deleteRuleMutation.isPending}
                            onClick={handleDelete}
                        >
                            Confirm Delete
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};
