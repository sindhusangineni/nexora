import React, { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Modal } from "@/shared/ui/Modal";
import { TaxonomySelector } from "./TaxonomySelector";
import { useCreateSelectionRule } from "../hooks/useAssessment";
import type {
    AssessmentSection,
    Difficulty,
    QuestionType,
    ScopeType,
} from "../types/assessment.types";

interface SelectionRuleEditorProps {
    assessmentId: string;
    sections: AssessmentSection[];
    existingRulesCount: number;
    isOpen: boolean;
    onClose: () => void;
}

export const SelectionRuleEditor: React.FC<SelectionRuleEditorProps> = ({
    assessmentId,
    sections,
    existingRulesCount,
    isOpen,
    onClose,
}) => {
    const [sectionId, setSectionId] = useState<string>("");
    const [scopeType, setScopeType] = useState<ScopeType>("TOPIC");
    const [scopeId, setScopeId] = useState<string>("");
    const [scopeLabel, setScopeLabel] = useState<string>("");
    const [questionType, setQuestionType] = useState<QuestionType | "">("");
    const [difficulty, setDifficulty] = useState<Difficulty | "">("");
    const [questionCount, setQuestionCount] = useState<number>(5);
    const [position, setPosition] = useState<number>(existingRulesCount);
    const [error, setError] = useState<string | null>(null);

    const createRuleMutation = useCreateSelectionRule(assessmentId);

    const handleTaxonomyChange = (
        newScopeType: ScopeType,
        newScopeId: string,
        newLabel: string,
    ) => {
        setScopeType(newScopeType);
        setScopeId(newScopeId);
        setScopeLabel(newLabel);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!scopeId) {
            setError(`Please select a specific ${scopeType.toLowerCase()} to define the rule scope.`);
            return;
        }

        if (questionCount < 1) {
            setError("Question count must be at least 1.");
            return;
        }

        try {
            await createRuleMutation.mutateAsync({
                assessment_section_id: sectionId ? sectionId : null,
                scope_type: scopeType,
                scope_id: scopeId,
                question_type: questionType ? (questionType as QuestionType) : null,
                difficulty: difficulty ? (difficulty as Difficulty) : null,
                question_count: questionCount,
                position,
            });
            onClose();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to create selection rule.";
            setError(message);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Add Question Selection Rule"
            maxWidth="lg"
        >
            <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                    <div className="p-3 text-xs text-danger bg-danger-surface rounded-md border border-danger/20">
                        {error}
                    </div>
                )}

                {/* Section selection */}
                {sections.length > 0 && (
                    <div>
                        <label
                            htmlFor="rule-section-select"
                            className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                        >
                            Target Section (Optional)
                        </label>
                        <select
                            id="rule-section-select"
                            value={sectionId}
                            onChange={(e) => setSectionId(e.target.value)}
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        >
                            <option value="">No Section (Assessment-wide)</option>
                            {sections.map((s) => (
                                <option key={s.id} value={s.id}>
                                    Section {s.position + 1}: {s.title}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Taxonomy Scope */}
                <div className="p-4 bg-neutral-50/70 border border-neutral-200 rounded-lg space-y-3">
                    <TaxonomySelector
                        scopeType={scopeType}
                        scopeId={scopeId}
                        onChange={handleTaxonomyChange}
                    />
                    {scopeLabel && (
                        <p className="text-xs font-medium text-primary">
                            Selected Target: <span className="font-semibold">{scopeLabel}</span>
                        </p>
                    )}
                </div>

                {/* Question Type & Difficulty Filters */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label
                            htmlFor="rule-question-type-select"
                            className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                        >
                            Question Type Filter
                        </label>
                        <select
                            id="rule-question-type-select"
                            value={questionType}
                            onChange={(e) =>
                                setQuestionType(e.target.value as QuestionType | "")
                            }
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        >
                            <option value="">Any question type</option>
                            <option value="MCQ">Multiple Choice (Single Answer)</option>
                            <option value="MULTIPLE_SELECT">Multiple Select</option>
                            <option value="TRUE_FALSE">True / False</option>
                            <option value="ASSERTION_REASON">Assertion and Reason</option>
                            <option value="MATCH_FOLLOWING">Match the Following</option>
                            <option value="DESCRIPTIVE">Descriptive / Long Answer</option>
                        </select>
                    </div>

                    <div>
                        <label
                            htmlFor="rule-difficulty-select"
                            className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                        >
                            Difficulty Filter
                        </label>
                        <select
                            id="rule-difficulty-select"
                            value={difficulty}
                            onChange={(e) =>
                                setDifficulty(e.target.value as Difficulty | "")
                            }
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        >
                            <option value="">Any difficulty</option>
                            <option value="EASY">Easy</option>
                            <option value="MEDIUM">Medium</option>
                            <option value="HARD">Hard</option>
                        </select>
                    </div>
                </div>

                {/* Question Count & Position */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                        label="Questions to Select"
                        type="number"
                        min={1}
                        required
                        value={questionCount}
                        onChange={(e) =>
                            setQuestionCount(parseInt(e.target.value, 10) || 1)
                        }
                        helperText="Target count of questions matching these criteria."
                    />

                    <Input
                        label="Rule Execution Position"
                        type="number"
                        min={0}
                        required
                        value={position}
                        onChange={(e) =>
                            setPosition(parseInt(e.target.value, 10) || 0)
                        }
                        helperText="Order in which this rule is evaluated (unique per assessment)."
                    />
                </div>

                {/* Deduplication helper callout */}
                <div className="p-3 bg-amber-50/80 border border-amber-200/80 rounded-md text-xs text-amber-900 leading-relaxed">
                    <span className="font-semibold">Deduplication notice: </span>
                    Overlapping rules may resolve to fewer questions because each question can appear only once in a generated paper.
                </div>

                <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                    <Button type="button" variant="secondary" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="primary"
                        loading={createRuleMutation.isPending}
                    >
                        Add Selection Rule
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
