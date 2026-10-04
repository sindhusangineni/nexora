import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Card } from "@/shared/ui/Card";
import { MarkingTimingConfiguration } from "./MarkingTimingConfiguration";
import { useCreateAssessment } from "../hooks/useAssessment";
import type {
    AssessmentType,
    ScoreFloorPolicy,
} from "../types/assessment.types";

interface AssessmentFormProps {
    onSuccess?: (assessmentId: string) => void;
}

export const AssessmentForm: React.FC<AssessmentFormProps> = ({ onSuccess }) => {
    const navigate = useNavigate();

    // Step state: 1 = Details, 2 = Timing & Marking
    const [step, setStep] = useState<1 | 2>(1);

    // Form fields
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [type, setType] = useState<AssessmentType>("PRACTICE");
    const [durationMinutes, setDurationMinutes] = useState<number>(120);
    const [marksPerQuestion, setMarksPerQuestion] = useState<string>("2.00");
    const [penaltyPerQuestion, setPenaltyPerQuestion] = useState<string>("0.66");
    const [scoreFloorPolicy, setScoreFloorPolicy] =
        useState<ScoreFloorPolicy>("UNRESTRICTED");

    const [error, setError] = useState<string | null>(null);

    const createMutation = useCreateAssessment();

    const handleNext = (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        if (!title.trim()) {
            setError("Assessment title is required.");
            return;
        }
        setStep(2);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        const durationSeconds = durationMinutes * 60;
        const marks = parseFloat(marksPerQuestion);
        const penalty = parseFloat(penaltyPerQuestion);

        if (durationSeconds < 1) {
            setError("Duration must be at least 1 minute.");
            return;
        }
        if (isNaN(marks) || marks <= 0) {
            setError("Marks per question must be greater than 0.");
            return;
        }
        if (isNaN(penalty) || penalty < 0) {
            setError("Penalty per question cannot be negative.");
            return;
        }

        try {
            const created = await createMutation.mutateAsync({
                title: title.trim(),
                description: description.trim(),
                type,
                duration_seconds: durationSeconds,
                marks_per_question: marks.toFixed(2),
                penalty_per_question: penalty.toFixed(2),
            });

            if (onSuccess) {
                onSuccess(created.id);
            } else {
                navigate(`/admin/assessments/${created.id}/edit`);
            }
        } catch (err: unknown) {
            const message =
                err instanceof Error ? err.message : "Failed to create assessment draft.";
            setError(message);
        }
    };

    return (
        <div className="space-y-6 max-w-3xl mx-auto">
            {/* Step Indicator */}
            <div className="flex items-center justify-between border-b border-border pb-4">
                <div className="flex items-center space-x-3">
                    <span
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                            step === 1
                                ? "bg-primary text-white"
                                : "bg-neutral-100 text-neutral-600"
                        }`}
                    >
                        1
                    </span>
                    <span
                        className={`text-sm font-medium ${
                            step === 1 ? "text-foreground font-semibold" : "text-foreground-muted"
                        }`}
                    >
                        Assessment Details
                    </span>
                </div>

                <div className="h-0.5 w-12 bg-neutral-200" />

                <div className="flex items-center space-x-3">
                    <span
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                            step === 2
                                ? "bg-primary text-white"
                                : "bg-neutral-100 text-neutral-600"
                        }`}
                    >
                        2
                    </span>
                    <span
                        className={`text-sm font-medium ${
                            step === 2 ? "text-foreground font-semibold" : "text-foreground-muted"
                        }`}
                    >
                        Timing & Marking
                    </span>
                </div>
            </div>

            {error && (
                <div className="p-3 text-xs text-danger bg-danger-surface rounded-md border border-danger/20">
                    {error}
                </div>
            )}

            {step === 1 ? (
                <Card className="p-6">
                    <form onSubmit={handleNext} className="space-y-5">
                        <div className="flex items-center justify-between">
                            <h3 className="text-base font-semibold text-foreground tracking-tight">
                                Step 1: Assessment Definition
                            </h3>
                            <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-neutral-100 text-neutral-700 border border-neutral-200">
                                Status: DRAFT
                            </span>
                        </div>

                        <Input
                            label="Assessment Title"
                            required
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g. UPSC Prelims General Studies Mock 01"
                            helperText="Clear, descriptive title for this assessment."
                            autoFocus
                        />

                        <div>
                            <label
                                htmlFor="assessment-desc"
                                className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                            >
                                Description / Instructions (Optional)
                            </label>
                            <textarea
                                id="assessment-desc"
                                rows={4}
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full px-3 py-2 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                                placeholder="Provide instructions, syllabus coverage, or guidance for candidates..."
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="assessment-type-select"
                                className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                            >
                                Assessment Type
                            </label>
                            <select
                                id="assessment-type-select"
                                value={type}
                                onChange={(e) => setType(e.target.value as AssessmentType)}
                                className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            >
                                <option value="PRACTICE">Practice</option>
                                <option value="REVISION">Revision</option>
                                <option value="MOCK">Mock</option>
                                <option value="CUSTOM">Custom</option>
                            </select>
                        </div>

                        <div className="flex justify-end pt-3 border-t border-border">
                            <Button type="submit" variant="primary">
                                Continue to Timing & Marking →
                            </Button>
                        </div>
                    </form>
                </Card>
            ) : (
                <Card className="p-6">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h3 className="text-base font-semibold text-foreground tracking-tight">
                                Step 2: Timing, Marks & Scoring Policy
                            </h3>
                            <span className="text-xs text-foreground-muted">
                                {title}
                            </span>
                        </div>

                        <MarkingTimingConfiguration
                            durationMinutes={durationMinutes}
                            onDurationMinutesChange={setDurationMinutes}
                            marksPerQuestion={marksPerQuestion}
                            onMarksPerQuestionChange={setMarksPerQuestion}
                            penaltyPerQuestion={penaltyPerQuestion}
                            onPenaltyPerQuestionChange={setPenaltyPerQuestion}
                            scoreFloorPolicy={scoreFloorPolicy}
                            onScoreFloorPolicyChange={setScoreFloorPolicy}
                        />

                        <div className="flex justify-between pt-4 border-t border-border">
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() => setStep(1)}
                            >
                                ← Back to Details
                            </Button>
                            <Button
                                type="submit"
                                variant="primary"
                                loading={createMutation.isPending}
                            >
                                Initialize Assessment Builder
                            </Button>
                        </div>
                    </form>
                </Card>
            )}
        </div>
    );
};
