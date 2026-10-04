import React from "react";
import type { DeliveryChoice } from "../../types/attempt.types";
import { CheckIcon } from "../Icons";

interface MultipleSelectResponseProps {
    choices: DeliveryChoice[];
    selectedChoiceIds: string[];
    onChange: (choiceIds: string[]) => void;
    disabled?: boolean;
}

export const MultipleSelectResponse: React.FC<MultipleSelectResponseProps> = ({
    choices,
    selectedChoiceIds,
    onChange,
    disabled = false,
}) => {
    const handleToggle = (choiceId: string) => {
        if (disabled) return;
        if (selectedChoiceIds.includes(choiceId)) {
            onChange(selectedChoiceIds.filter((id) => id !== choiceId));
        } else {
            onChange([...selectedChoiceIds, choiceId]);
        }
    };

    return (
        <fieldset className="space-y-2.5" disabled={disabled}>
            <legend className="sr-only">Multiple Select Options</legend>
            <div className="text-xs text-foreground-muted mb-2 font-medium">
                Select all options that apply:
            </div>
            {choices.map((choice, idx) => {
                const isSelected = selectedChoiceIds.includes(choice.id);
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
                            type="checkbox"
                            value={choice.id}
                            checked={isSelected}
                            onChange={() => handleToggle(choice.id)}
                            disabled={disabled}
                            className="sr-only"
                        />
                        <div
                            className={`flex items-center justify-center w-6 h-6 rounded-md text-xs font-semibold shrink-0 mr-3 border transition-colors ${
                                isSelected
                                    ? "bg-primary text-white border-primary"
                                    : "bg-neutral-100 text-neutral-700 border-neutral-200"
                            }`}
                        >
                            {isSelected ? (
                                <CheckIcon className="w-3.5 h-3.5" />
                            ) : (
                                letter
                            )}
                        </div>
                        <span className="flex-1 pt-0.5 leading-relaxed">{choice.text}</span>
                    </label>
                );
            })}
        </fieldset>
    );
};
