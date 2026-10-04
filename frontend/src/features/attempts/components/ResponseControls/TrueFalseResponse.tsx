import React from "react";

interface TrueFalseResponseProps {
    value: boolean | null;
    onChange: (val: boolean) => void;
    disabled?: boolean;
}

export const TrueFalseResponse: React.FC<TrueFalseResponseProps> = ({
    value,
    onChange,
    disabled = false,
}) => {
    return (
        <fieldset className="space-y-3" disabled={disabled}>
            <legend className="sr-only">True or False Selection</legend>
            <div className="grid grid-cols-2 gap-4">
                <button
                    type="button"
                    onClick={() => onChange(true)}
                    disabled={disabled}
                    className={`flex items-center justify-center p-4 rounded-lg border text-sm font-semibold transition-all cursor-pointer ${
                        value === true
                            ? "bg-primary-50/50 border-primary text-primary-700 shadow-2xs ring-1 ring-primary"
                            : "bg-surface border-border text-neutral-800 hover:border-neutral-300"
                    } ${disabled ? "opacity-75 cursor-not-allowed" : ""}`}
                    aria-pressed={value === true}
                >
                    True
                </button>

                <button
                    type="button"
                    onClick={() => onChange(false)}
                    disabled={disabled}
                    className={`flex items-center justify-center p-4 rounded-lg border text-sm font-semibold transition-all cursor-pointer ${
                        value === false
                            ? "bg-primary-50/50 border-primary text-primary-700 shadow-2xs ring-1 ring-primary"
                            : "bg-surface border-border text-neutral-800 hover:border-neutral-300"
                    } ${disabled ? "opacity-75 cursor-not-allowed" : ""}`}
                    aria-pressed={value === false}
                >
                    False
                </button>
            </div>
        </fieldset>
    );
};
