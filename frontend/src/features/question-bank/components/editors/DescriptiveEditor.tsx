export interface DescriptiveEditorProps {
    marks: number;
    expectedAnswer: string;
    onChange: (data: { marks: number; expectedAnswer: string }) => void;
    disabled?: boolean;
    errors?: {
        marks?: string;
        expectedAnswer?: string;
    };
}

export function DescriptiveEditor({
    marks,
    expectedAnswer,
    onChange,
    disabled = false,
    errors,
}: DescriptiveEditorProps) {
    return (
        <div className="space-y-4">
            <div>
                <h4 className="text-sm font-semibold text-foreground tracking-tight">
                    Descriptive Grading Rubric & Reference Answer
                </h4>
                <p className="text-xs text-foreground-muted">
                    Specify the maximum marks allocated and provide the benchmark reference answer or grading criteria.
                </p>
            </div>

            {/* Marks */}
            <div className="space-y-1.5 max-w-xs">
                <label
                    htmlFor="desc-marks"
                    className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                >
                    Maximum Allocated Marks
                </label>
                <input
                    id="desc-marks"
                    type="number"
                    min={1}
                    max={100}
                    value={marks || ""}
                    onChange={(e) =>
                        onChange({
                            marks: Math.max(1, parseInt(e.target.value, 10) || 1),
                            expectedAnswer,
                        })
                    }
                    disabled={disabled}
                    placeholder="e.g. 10, 15, 20"
                    className={`w-full h-10 px-3 text-sm rounded-lg border bg-surface text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 ${
                        errors?.marks ? "border-danger" : "border-border"
                    }`}
                />
                {errors?.marks && (
                    <p className="text-xs font-medium text-danger" role="alert">
                        {errors.marks}
                    </p>
                )}
            </div>

            {/* Expected Answer / Rubric */}
            <div className="space-y-1.5">
                <label
                    htmlFor="desc-expected-answer"
                    className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                >
                    Expected Answer & Evaluation Rubric
                </label>
                <textarea
                    id="desc-expected-answer"
                    rows={5}
                    value={expectedAnswer}
                    onChange={(e) =>
                        onChange({ marks, expectedAnswer: e.target.value })
                    }
                    disabled={disabled}
                    placeholder="Provide reference points, key arguments, structure requirements, and criteria for full marks..."
                    className={`w-full p-3 text-sm rounded-lg border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 leading-relaxed ${
                        errors?.expectedAnswer ? "border-danger" : "border-border"
                    }`}
                />
                {errors?.expectedAnswer && (
                    <p className="text-xs font-medium text-danger" role="alert">
                        {errors.expectedAnswer}
                    </p>
                )}
            </div>
        </div>
    );
}
