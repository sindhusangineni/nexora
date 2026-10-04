import React from "react";
import type { DeliveryChoice } from "../../types/attempt.types";

interface McqResponseProps {
    choices: DeliveryChoice[];
    selectedChoiceId: string | null;
    onChange: (choiceId: string) => void;
    disabled?: boolean;
}

export const McqResponse: React.FC<McqResponseProps> = ({
    choices,
    selectedChoiceId,
    onChange,
    disabled = false,
}) => {
    return (
        <fieldset className="space-y-2.5" disabled={disabled}>
            <legend className="sr-only">Multiple Choice Options</legend>
            {choices.map((choice, idx) => {
                const isSelected = selectedChoiceId === choice.id;
                const letter = String.fromCharCode(65 + idx);

                return (
                    <label
                        key={choice.id}
                        className={`flex items-start p-3.5 rounded-lg border text-sm transition-all cursor-pointer ${
                            isSelected
                                ? "bg-primary-50/40 border-primary text-neutral-900 shadow-2xs"
                                : "bg-surface border-border text-neutral-800 hover:border-neutral-300"
                        } ${disabled ? "opacity-75 cursor-not-allowed" : ""}`}
                    >
                        <input
                            type="radio"
                            name="mcq-choice"
                            value={choice.id}
                            checked={isSelected}
                            onChange={() => onChange(choice.id)}
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
                        <span className="flex-1 pt-0.5 leading-relaxed">{choice.text}</span>
                    </label>
                );
            })}
        </fieldset>
    );
};
