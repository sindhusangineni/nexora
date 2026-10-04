import { Badge } from "@/shared/ui/Badge";
import type {
    AssertionReasonRelationship,
    Difficulty,
    QuestionType,
} from "../../types/questionBank.types";

export interface StudentSafeQuestionData {
    id: string;
    text: string;
    question_type: QuestionType;
    difficulty?: Difficulty;
    content?: {
        choices?: Array<{ id: string; text: string; position: number }>;
        assertion?: string;
        reason?: string;
        left_items?: Array<{ id: string; text: string; position: number }>;
        right_items?: Array<{ id: string; text: string; position: number }>;
        marks?: number;
    };
}

export interface QuestionRendererProps {
    question: StudentSafeQuestionData;
    questionNumber?: number;
    value?: unknown;
    onChange?: (val: unknown) => void;
    disabled?: boolean;
    className?: string;
}

export function QuestionRenderer({
    question,
    questionNumber,
    value,
    onChange,
    disabled = false,
    className = "",
}: QuestionRendererProps) {
    const qType = question.question_type;
    const content = question.content || {};

    const optionLetters = ["A", "B", "C", "D", "E", "F", "G", "H"];

    return (
        <div
            className={`space-y-6 select-none bg-surface p-6 sm:p-8 rounded-xl border border-border shadow-xs ${className}`}
            data-testid="student-question-renderer"
        >
            {/* Header: Question Number & Difficulty Badge only */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-3">
                    {questionNumber && (
                        <span className="font-mono text-sm font-bold px-2.5 py-1 rounded bg-neutral-100 text-neutral-800">
                            Q {questionNumber}
                        </span>
                    )}
                    <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                        {qType.replace("_", " ")}
                    </span>
                </div>

                {content.marks && (
                    <Badge variant="outline" size="sm">
                        {content.marks} Marks
                    </Badge>
                )}
            </div>

            {/* Stem Text */}
            <div className="text-base sm:text-lg font-medium text-foreground leading-relaxed whitespace-pre-wrap">
                {question.text}
            </div>

            {/* MCQ (Single Choice) */}
            {qType === "MCQ" && content.choices && (
                <div className="space-y-2.5" role="radiogroup" aria-label="Question choices">
                    {content.choices.map((choice, idx) => {
                        const letter = optionLetters[idx] || `${idx + 1}`;
                        const isSelected = value === choice.id;

                        return (
                            <div
                                key={choice.id}
                                onClick={() => !disabled && onChange?.(choice.id)}
                                role="radio"
                                aria-checked={isSelected}
                                tabIndex={disabled ? -1 : 0}
                                onKeyDown={(e) => {
                                    if ((e.key === "Enter" || e.key === " ") && !disabled) {
                                        e.preventDefault();
                                        onChange?.(choice.id);
                                    }
                                }}
                                className={`flex items-start gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
                                    isSelected
                                        ? "bg-primary-50/70 border-primary-500 ring-2 ring-primary-500/20"
                                        : "bg-surface border-border hover:bg-surface-muted hover:border-neutral-300"
                                } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
                            >
                                <span
                                    className={`w-7 h-7 rounded-md font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 ${
                                        isSelected
                                            ? "bg-primary-600 text-white"
                                            : "bg-neutral-100 text-neutral-700"
                                    }`}
                                >
                                    {letter}
                                </span>
                                <span className="text-sm text-foreground leading-relaxed pt-0.5">
                                    {choice.text}
                                </span>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* MULTIPLE_SELECT */}
            {qType === "MULTIPLE_SELECT" && content.choices && (
                <div className="space-y-3">
                    <p className="text-xs text-foreground-muted font-medium">
                        Select all correct options that apply:
                    </p>
                    <div className="space-y-2.5">
                        {content.choices.map((choice, idx) => {
                            const letter = optionLetters[idx] || `${idx + 1}`;
                            const selectedIds = Array.isArray(value) ? (value as string[]) : [];
                            const isSelected = selectedIds.includes(choice.id);

                            const handleToggle = () => {
                                if (disabled) return;
                                const next = isSelected
                                    ? selectedIds.filter((id) => id !== choice.id)
                                    : [...selectedIds, choice.id];
                                onChange?.(next);
                            };

                            return (
                                <div
                                    key={choice.id}
                                    onClick={handleToggle}
                                    role="checkbox"
                                    aria-checked={isSelected}
                                    tabIndex={disabled ? -1 : 0}
                                    onKeyDown={(e) => {
                                        if ((e.key === "Enter" || e.key === " ") && !disabled) {
                                            e.preventDefault();
                                            handleToggle();
                                        }
                                    }}
                                    className={`flex items-start gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
                                        isSelected
                                            ? "bg-primary-50/70 border-primary-500 ring-2 ring-primary-500/20"
                                            : "bg-surface border-border hover:bg-surface-muted hover:border-neutral-300"
                                    } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
                                >
                                    <span
                                        className={`w-7 h-7 rounded-md font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 ${
                                            isSelected
                                                ? "bg-primary-600 text-white"
                                                : "bg-neutral-100 text-neutral-700"
                                        }`}
                                    >
                                        {isSelected ? "✓" : letter}
                                    </span>
                                    <span className="text-sm text-foreground leading-relaxed pt-0.5">
                                        {choice.text}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* TRUE_FALSE */}
            {qType === "TRUE_FALSE" && (
                <div className="grid grid-cols-2 gap-4 max-w-md pt-2">
                    <button
                        type="button"
                        disabled={disabled}
                        onClick={() => onChange?.(true)}
                        className={`py-3.5 px-6 rounded-xl border text-sm font-bold transition-all ${
                            value === true
                                ? "bg-emerald-600 text-white border-emerald-600 ring-2 ring-emerald-500/20 shadow-xs"
                                : "bg-surface text-foreground border-border hover:bg-surface-muted"
                        } disabled:opacity-50`}
                    >
                        TRUE
                    </button>
                    <button
                        type="button"
                        disabled={disabled}
                        onClick={() => onChange?.(false)}
                        className={`py-3.5 px-6 rounded-xl border text-sm font-bold transition-all ${
                            value === false
                                ? "bg-red-600 text-white border-red-600 ring-2 ring-red-500/20 shadow-xs"
                                : "bg-surface text-foreground border-border hover:bg-surface-muted"
                        } disabled:opacity-50`}
                    >
                        FALSE
                    </button>
                </div>
            )}

            {/* ASSERTION_REASON */}
            {qType === "ASSERTION_REASON" && (
                <div className="space-y-5">
                    <div className="space-y-3">
                        {content.assertion && (
                            <div className="p-4 rounded-lg bg-surface-muted/60 border border-border space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-primary-700 block">
                                    Assertion (A)
                                </span>
                                <p className="text-sm text-foreground leading-relaxed">
                                    {content.assertion}
                                </p>
                            </div>
                        )}

                        {content.reason && (
                            <div className="p-4 rounded-lg bg-surface-muted/60 border border-border space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-primary-700 block">
                                    Reason (R)
                                </span>
                                <p className="text-sm text-foreground leading-relaxed">
                                    {content.reason}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Standard UPSC Assertion-Reason Options */}
                    <div className="space-y-2.5">
                        {[
                            {
                                code: "BOTH_TRUE_REASON_CORRECT",
                                label: "Both (A) and (R) are true, and (R) is the correct explanation of (A)",
                            },
                            {
                                code: "BOTH_TRUE_REASON_NOT_CORRECT",
                                label: "Both (A) and (R) are true, but (R) is NOT the correct explanation of (A)",
                            },
                            {
                                code: "ASSERTION_TRUE_REASON_FALSE",
                                label: "(A) is true, but (R) is false",
                            },
                            {
                                code: "ASSERTION_FALSE_REASON_FALSE",
                                label: "(A) is false, and (R) is false",
                            },
                        ].map((opt, idx) => {
                            const letter = optionLetters[idx];
                            const isSelected = value === opt.code;

                            return (
                                <div
                                    key={opt.code}
                                    onClick={() =>
                                        !disabled &&
                                        onChange?.(opt.code as AssertionReasonRelationship)
                                    }
                                    role="radio"
                                    aria-checked={isSelected}
                                    tabIndex={disabled ? -1 : 0}
                                    className={`flex items-start gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
                                        isSelected
                                            ? "bg-primary-50/70 border-primary-500 ring-2 ring-primary-500/20"
                                            : "bg-surface border-border hover:bg-surface-muted hover:border-neutral-300"
                                    } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
                                >
                                    <span
                                        className={`w-7 h-7 rounded-md font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 ${
                                            isSelected
                                                ? "bg-primary-600 text-white"
                                                : "bg-neutral-100 text-neutral-700"
                                        }`}
                                    >
                                        {letter}
                                    </span>
                                    <span className="text-sm text-foreground leading-relaxed pt-0.5">
                                        {opt.label}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* MATCH_FOLLOWING */}
            {qType === "MATCH_FOLLOWING" &&
                content.left_items &&
                content.right_items &&
                (() => {
                    const normalizedLeft = (content.left_items as unknown[]).map(
                        (item, idx) => {
                            if (typeof item === "string") {
                                return {
                                    id: `left-${idx + 1}`,
                                    text: item,
                                    position: idx + 1,
                                };
                            }
                            const obj = item as {
                                id?: string;
                                text: string;
                                position?: number;
                            };
                            return {
                                id: obj.id || `left-${idx + 1}`,
                                text: obj.text,
                                position: obj.position ?? idx + 1,
                            };
                        },
                    );
                    const normalizedRight = (content.right_items as unknown[]).map(
                        (item, idx) => {
                            if (typeof item === "string") {
                                return {
                                    id: `right-${idx + 1}`,
                                    text: item,
                                    position: idx + 1,
                                };
                            }
                            const obj = item as {
                                id?: string;
                                text: string;
                                position?: number;
                            };
                            return {
                                id: obj.id || `right-${idx + 1}`,
                                text: obj.text,
                                position: obj.position ?? idx + 1,
                            };
                        },
                    );

                    return (
                        <div className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="p-4 rounded-xl border border-border bg-surface-muted/40 space-y-2">
                                    <span className="text-xs font-bold uppercase tracking-wider text-neutral-500 block">
                                        Column I
                                    </span>
                                    {normalizedLeft.map((i) => (
                                        <div
                                            key={i.id}
                                            className="flex items-center gap-2 p-2 bg-surface rounded-md border border-border text-xs"
                                        >
                                            <span className="w-5 h-5 rounded bg-neutral-200 text-neutral-800 font-bold flex items-center justify-center text-[10px]">
                                                {i.position}
                                            </span>
                                            <span className="font-medium text-foreground">
                                                {i.text}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                <div className="p-4 rounded-xl border border-border bg-surface-muted/40 space-y-2">
                                    <span className="text-xs font-bold uppercase tracking-wider text-neutral-500 block">
                                        Column II
                                    </span>
                                    {normalizedRight.map((i, idx) => (
                                        <div
                                            key={i.id}
                                            className="flex items-center gap-2 p-2 bg-surface rounded-md border border-border text-xs"
                                        >
                                            <span className="w-5 h-5 rounded bg-neutral-200 text-neutral-800 font-bold flex items-center justify-center text-[10px]">
                                                {optionLetters[idx] || i.position}
                                            </span>
                                            <span className="font-medium text-foreground">
                                                {i.text}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Candidate Pair Selection */}
                            <div className="p-4 rounded-xl border border-border bg-surface space-y-3">
                                <span className="text-xs font-bold uppercase tracking-wider text-foreground block">
                                    Select Your Matching Pairs
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                                    {normalizedLeft.map((leftItem) => {
                                        const currentPairs = Array.isArray(value)
                                            ? (value as Array<{
                                                  left_position: number;
                                                  right_position: number;
                                              }>)
                                            : [];
                                        const matched = currentPairs.find(
                                            (p) => p.left_position === leftItem.position,
                                        );
                                        const selectedRightPos =
                                            matched?.right_position ?? "";

                                        const handleSelect = (rPos: number) => {
                                            if (disabled) return;
                                            const otherPairs = currentPairs.filter(
                                                (p) =>
                                                    p.left_position !==
                                                    leftItem.position,
                                            );
                                            onChange?.([
                                                ...otherPairs,
                                                {
                                                    left_position: leftItem.position,
                                                    right_position: rPos,
                                                },
                                            ]);
                                        };

                                        return (
                                            <div
                                                key={leftItem.position}
                                                className="flex items-center justify-between p-2 rounded-lg border border-border bg-surface-muted/50 text-xs"
                                            >
                                                <span className="font-semibold text-neutral-800">
                                                    Item {leftItem.position} →
                                                </span>
                                                <select
                                                    aria-label={`Match for Column I item ${leftItem.position}`}
                                                    value={selectedRightPos}
                                                    disabled={disabled}
                                                    onChange={(e) =>
                                                        handleSelect(
                                                            parseInt(
                                                                e.target.value,
                                                                10,
                                                            ),
                                                        )
                                                    }
                                                    className="h-8 px-2 rounded border border-border bg-surface font-semibold text-foreground text-xs focus:ring-1 focus:ring-primary-500"
                                                >
                                                    <option value="" disabled>
                                                        Select
                                                    </option>
                                                    {normalizedRight.map(
                                                        (rightItem, idx) => (
                                                            <option
                                                                key={rightItem.id}
                                                                value={
                                                                    rightItem.position
                                                                }
                                                            >
                                                                {optionLetters[
                                                                    idx
                                                                ] ||
                                                                    rightItem.position}
                                                            </option>
                                                        ),
                                                    )}
                                                </select>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    );
                })()}

            {/* DESCRIPTIVE */}
            {qType === "DESCRIPTIVE" && (
                <div className="space-y-3">
                    <label
                        htmlFor="student-descriptive-answer"
                        className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                    >
                        Your Answer
                    </label>
                    <textarea
                        id="student-descriptive-answer"
                        rows={8}
                        value={(value as string) || ""}
                        onChange={(e) => onChange?.(e.target.value)}
                        disabled={disabled}
                        placeholder="Type your response here..."
                        className="w-full p-4 text-sm rounded-xl border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 leading-relaxed font-sans"
                    />
                    <div className="flex justify-end text-xs text-foreground-muted">
                        <span>
                            {((value as string) || "").trim() ? ((value as string) || "").trim().split(/\s+/).length : 0} words
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
