import React from "react";
import { Input } from "@/shared/ui/Input";
import type { ScoreFloorPolicy } from "../types/assessment.types";

interface MarkingTimingConfigurationProps {
    durationMinutes: number;
    onDurationMinutesChange: (minutes: number) => void;
    marksPerQuestion: string;
    onMarksPerQuestionChange: (marks: string) => void;
    penaltyPerQuestion: string;
    onPenaltyPerQuestionChange: (penalty: string) => void;
    scoreFloorPolicy: ScoreFloorPolicy;
    onScoreFloorPolicyChange: (policy: ScoreFloorPolicy) => void;
    disabled?: boolean;
}

export const MarkingTimingConfiguration: React.FC<MarkingTimingConfigurationProps> = ({
    durationMinutes,
    onDurationMinutesChange,
    marksPerQuestion,
    onMarksPerQuestionChange,
    penaltyPerQuestion,
    onPenaltyPerQuestionChange,
    scoreFloorPolicy,
    onScoreFloorPolicyChange,
    disabled = false,
}) => {
    return (
        <div className="space-y-6">
            {/* Timing Section */}
            <div className="space-y-3">
                <h4 className="text-xs font-semibold text-neutral-700 uppercase tracking-wider">
                    Timing Configuration
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                        label="Assessment Duration (Minutes)"
                        type="number"
                        min={1}
                        required
                        disabled={disabled}
                        value={durationMinutes}
                        onChange={(e) =>
                            onDurationMinutesChange(Math.max(1, parseInt(e.target.value, 10) || 1))
                        }
                        helperText={`Equates to ${(durationMinutes * 60).toLocaleString()} seconds`}
                    />
                </div>
            </div>

            {/* Marking Configuration */}
            <div className="space-y-3">
                <h4 className="text-xs font-semibold text-neutral-700 uppercase tracking-wider">
                    Marking Scheme
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                        label="Marks per Correct Answer"
                        type="number"
                        step="0.01"
                        min={0.01}
                        required
                        disabled={disabled}
                        value={marksPerQuestion}
                        onChange={(e) => onMarksPerQuestionChange(e.target.value)}
                        helperText="Awarded points for each correctly answered item (e.g. 2.00)."
                    />

                    <Input
                        label="Penalty per Incorrect Answer"
                        type="number"
                        step="0.01"
                        min={0}
                        required
                        disabled={disabled}
                        value={penaltyPerQuestion}
                        onChange={(e) => onPenaltyPerQuestionChange(e.target.value)}
                        helperText="Deducted marks for incorrect answers (e.g. 0.66). Set 0.00 for no penalty."
                    />
                </div>
            </div>

            {/* Scoring Floor Policy */}
            <div className="space-y-3">
                <label
                    htmlFor="score-floor-policy-select"
                    className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                >
                    Scoring Floor Policy
                </label>
                <select
                    id="score-floor-policy-select"
                    value={scoreFloorPolicy}
                    disabled={disabled}
                    onChange={(e) =>
                        onScoreFloorPolicyChange(e.target.value as ScoreFloorPolicy)
                    }
                    className="w-full sm:w-80 h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
                >
                    <option value="UNRESTRICTED">Unrestricted</option>
                    <option value="ZERO_FLOOR_TOTAL">Zero Floor — Total</option>
                    <option value="ZERO_FLOOR_SECTION">Zero Floor — Section</option>
                </select>

                <div className="p-3.5 bg-neutral-50 rounded-md border border-neutral-200 text-xs text-foreground-muted space-y-1">
                    {scoreFloorPolicy === "UNRESTRICTED" && (
                        <div>
                            <span className="font-semibold text-neutral-800">
                                Unrestricted:
                            </span>{" "}
                            Negative marks can accumulate freely, allowing the final total score to fall below zero.
                        </div>
                    )}
                    {scoreFloorPolicy === "ZERO_FLOOR_TOTAL" && (
                        <div>
                            <span className="font-semibold text-neutral-800">
                                Zero Floor — Total:
                            </span>{" "}
                            The final candidate overall score cannot fall below 0.00, regardless of penalties.
                        </div>
                    )}
                    {scoreFloorPolicy === "ZERO_FLOOR_SECTION" && (
                        <div>
                            <span className="font-semibold text-neutral-800">
                                Zero Floor — Section:
                            </span>{" "}
                            Each section score cannot fall below 0.00, preventing penalties in one section from cannibalizing marks earned in another.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
