import React from "react";

interface DescriptiveResponseProps {
    value: string | null;
    onChange: (text: string) => void;
    disabled?: boolean;
}

export const DescriptiveResponse: React.FC<DescriptiveResponseProps> = ({
    value,
    onChange,
    disabled = false,
}) => {
    const text = value || "";
    const trimmed = text.trim();
    const wordCount = trimmed ? trimmed.split(/\s+/).length : 0;
    const charCount = text.length;

    return (
        <div className="space-y-2">
            <label htmlFor="descriptive-answer" className="sr-only">
                Written Response
            </label>
            <textarea
                id="descriptive-answer"
                rows={8}
                value={text}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                placeholder="Type your comprehensive written answer here..."
                className="w-full p-4 bg-surface border border-border rounded-lg text-sm text-neutral-900 leading-relaxed placeholder:text-neutral-400 focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-75 disabled:cursor-not-allowed resize-y transition-all"
            />
            <div className="flex items-center justify-between text-xs text-foreground-muted">
                <span>
                    {wordCount} {wordCount === 1 ? "word" : "words"} • {charCount} characters
                </span>
                <span className="italic">
                    Manual evaluation will be completed after submission.
                </span>
            </div>
        </div>
    );
};
