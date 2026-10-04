export interface TrueFalseEditorProps {
    answer: boolean;
    onChange: (answer: boolean) => void;
    disabled?: boolean;
    error?: string;
}

export function TrueFalseEditor({
    answer,
    onChange,
    disabled = false,
    error,
}: TrueFalseEditorProps) {
    return (
        <div className="space-y-3">
            <div>
                <h4 className="text-sm font-semibold text-foreground tracking-tight">
                    Correct Statement Truth Value
                </h4>
                <p className="text-xs text-foreground-muted">
                    Specify whether the statement presented in the question stem is factually True or False.
                </p>
            </div>

            {error && (
                <p className="text-xs font-medium text-danger" role="alert">
                    {error}
                </p>
            )}

            <div className="flex items-center gap-4">
                <button
                    type="button"
                    onClick={() => onChange(true)}
                    disabled={disabled}
                    className={`flex-1 py-3 px-4 rounded-lg border text-sm font-bold transition-all ${
                        answer === true
                            ? "bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-500/20"
                            : "bg-surface text-neutral-700 border-border hover:bg-surface-muted"
                    } disabled:opacity-50`}
                >
                    <span className="flex items-center justify-center gap-2">
                        {answer === true && <span>✓</span>}
                        <span>TRUE</span>
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => onChange(false)}
                    disabled={disabled}
                    className={`flex-1 py-3 px-4 rounded-lg border text-sm font-bold transition-all ${
                        answer === false
                            ? "bg-red-600 text-white border-red-600 shadow-xs ring-2 ring-red-500/20"
                            : "bg-surface text-neutral-700 border-border hover:bg-surface-muted"
                    } disabled:opacity-50`}
                >
                    <span className="flex items-center justify-center gap-2">
                        {answer === false && <span>✕</span>}
                        <span>FALSE</span>
                    </span>
                </button>
            </div>
        </div>
    );
}
