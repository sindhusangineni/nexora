import React from "react";
import { AssertionReasonResponseEnum } from "../../types/attempt.types";

interface AssertionReasonResponseProps {
    assertion?: string;
    reason?: string;
    value: string | null;
    onChange: (val: string) => void;
    disabled?: boolean;
}

const OPTIONS = [
    {
        key: AssertionReasonResponseEnum.BOTH_TRUE_REASON_CORRECT,
        label: "Both Assertion (A) and Reason (R) are true, and Reason is the correct explanation of Assertion.",
    },
    {
        key: AssertionReasonResponseEnum.BOTH_TRUE_REASON_NOT_CORRECT,
        label: "Both Assertion (A) and Reason (R) are true, but Reason is NOT the correct explanation of Assertion.",
    },
    {
        key: AssertionReasonResponseEnum.ASSERTION_TRUE_REASON_FALSE,
        label: "Assertion (A) is true, but Reason (R) is false.",
    },
    {
        key: AssertionReasonResponseEnum.ASSERTION_FALSE_REASON_FALSE,
        label: "Assertion (A) is false, and Reason (R) is false.",
    },
];

export const AssertionReasonResponse: React.FC<AssertionReasonResponseProps> = ({
    assertion,
    reason,
    value,
    onChange,
    disabled = false,
}) => {
    return (
        <div className="space-y-4">
            {/* Context cards for Assertion & Reason */}
            {(assertion || reason) && (
                <div className="space-y-2 p-4 bg-neutral-50/70 border border-neutral-200 rounded-lg text-sm">
                    {assertion && (
                        <div>
                            <span className="font-semibold text-neutral-900 block text-xs tracking-wider uppercase text-foreground-muted mb-0.5">
                                Assertion (A):
                            </span>
                            <p className="text-neutral-800 leading-relaxed">{assertion}</p>
                        </div>
                    )}
                    {reason && (
                        <div className="pt-2 border-t border-neutral-200/60">
                            <span className="font-semibold text-neutral-900 block text-xs tracking-wider uppercase text-foreground-muted mb-0.5">
                                Reason (R):
                            </span>
                            <p className="text-neutral-800 leading-relaxed">{reason}</p>
                        </div>
                    )}
                </div>
            )}

            <fieldset className="space-y-2.5" disabled={disabled}>
                <legend className="sr-only">Assertion and Reason relationship options</legend>
                {OPTIONS.map((opt, idx) => {
                    const isSelected = value === opt.key;
                    const letter = String.fromCharCode(65 + idx);

                    return (
                        <label
                            key={opt.key}
                            className={`flex items-start p-3.5 rounded-lg border text-sm transition-all cursor-pointer ${
                                isSelected
                                    ? "bg-primary-50/40 border-primary text-neutral-900 shadow-2xs"
                                    : "bg-surface border-border text-neutral-800 hover:border-neutral-300"
                            } ${disabled ? "opacity-75 cursor-not-allowed" : ""}`}
                        >
                            <input
                                type="radio"
                                name="assertion-reason-option"
                                value={opt.key}
                                checked={isSelected}
                                onChange={() => onChange(opt.key)}
                                disabled={disabled}
                                className="sr-only"
                            />
                            <span
                                className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold shrink-0 mr-3 border transition-colors ${
                                    isSelected
                                        ? "bg-primary text-white border-primary"
                                        : "bg-neutral-100 text-neutral-700 border-neutral-200"
                                }`}
                            >
                                {letter}
                            </span>
                            <span className="flex-1 pt-0.5 leading-relaxed">{opt.label}</span>
                        </label>
                    );
                })}
            </fieldset>
        </div>
    );
};
