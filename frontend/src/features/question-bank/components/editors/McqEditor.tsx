import { Button } from "@/shared/ui/Button";
import type { ChoiceItem } from "../../types/questionBank.types";

export interface McqEditorProps {
    choices: ChoiceItem[];
    onChange: (choices: ChoiceItem[]) => void;
    disabled?: boolean;
    error?: string;
}

export function McqEditor({
    choices,
    onChange,
    disabled = false,
    error,
}: McqEditorProps) {
    const handleTextChange = (index: number, text: string) => {
        const next = choices.map((c, i) =>
            i === index ? { ...c, text, position: i + 1 } : { ...c, position: i + 1 },
        );
        onChange(next);
    };

    const handleSelectCorrect = (index: number) => {
        const next = choices.map((c, i) => ({
            ...c,
            position: i + 1,
            is_correct: i === index,
        }));
        onChange(next);
    };

    const handleAddOption = () => {
        const next: ChoiceItem[] = [
            ...choices,
            { text: "", position: choices.length + 1, is_correct: false },
        ];
        onChange(next);
    };

    const handleRemoveOption = (index: number) => {
        if (choices.length <= 2) return;
        const next = choices
            .filter((_, i) => i !== index)
            .map((c, i) => ({ ...c, position: i + 1 }));
        // If the removed one was correct, mark the first one as correct
        if (choices[index]?.is_correct && next.length > 0 && !next.some((c) => c.is_correct)) {
            next[0].is_correct = true;
        }
        onChange(next);
    };

    const optionLabels = ["A", "B", "C", "D", "E", "F", "G", "H"];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-semibold text-foreground tracking-tight">
                        Multiple Choice Options
                    </h4>
                    <p className="text-xs text-foreground-muted">
                        Define at least two options and mark exactly one option as the correct answer.
                    </p>
                </div>
                <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={handleAddOption}
                    disabled={disabled || choices.length >= 8}
                >
                    + Add option
                </Button>
            </div>

            {error && (
                <p className="text-xs font-medium text-danger" role="alert">
                    {error}
                </p>
            )}

            <div className="space-y-3">
                {choices.map((choice, index) => {
                    const label = optionLabels[index] || `${index + 1}`;
                    return (
                        <div
                            key={index}
                            className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                                choice.is_correct
                                    ? "bg-primary-50/50 border-primary-200"
                                    : "bg-surface border-border hover:border-border-strong"
                            }`}
                        >
                            <span className="w-7 h-7 rounded-md bg-neutral-100 text-neutral-700 flex items-center justify-center font-bold text-xs shrink-0 select-none">
                                {label}
                            </span>

                            <input
                                type="text"
                                value={choice.text}
                                onChange={(e) => handleTextChange(index, e.target.value)}
                                disabled={disabled}
                                placeholder={`Option ${label} text...`}
                                aria-label={`Option ${label} text`}
                                className="flex-1 h-9 px-3 text-sm rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50"
                            />

                            <label
                                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md cursor-pointer select-none text-xs font-medium transition-colors ${
                                    choice.is_correct
                                        ? "bg-primary-600 text-white shadow-xs"
                                        : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                                }`}
                            >
                                <input
                                    type="radio"
                                    name="mcq-correct-choice"
                                    checked={Boolean(choice.is_correct)}
                                    onChange={() => handleSelectCorrect(index)}
                                    disabled={disabled}
                                    className="sr-only"
                                />
                                <span>{choice.is_correct ? "● Correct" : "○ Mark Correct"}</span>
                            </label>

                            {choices.length > 2 && (
                                <button
                                    type="button"
                                    onClick={() => handleRemoveOption(index)}
                                    disabled={disabled}
                                    title={`Remove option ${label}`}
                                    aria-label={`Remove option ${label}`}
                                    className="p-1.5 rounded-md text-foreground-muted hover:text-danger hover:bg-red-50 transition-colors disabled:opacity-50"
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
