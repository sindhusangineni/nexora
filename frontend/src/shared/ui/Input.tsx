import { forwardRef, useId, type InputHTMLAttributes } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string | string[];
    helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
    { label, error, helperText, id, required, disabled, className = "", ...props },
    ref,
) {
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    const errorMessage = Array.isArray(error) ? error.join(" ") : error;
    const hasError = Boolean(errorMessage);

    const describedBy = [
        hasError ? errorId : null,
        helperText && !hasError ? helperId : null,
    ]
        .filter(Boolean)
        .join(" ") || undefined;

    return (
        <div className="w-full space-y-1.5">
            {label && (
                <label
                    htmlFor={inputId}
                    className="block text-sm font-medium text-foreground tracking-tight"
                >
                    {label}
                    {required && <span className="text-danger ml-0.5" aria-hidden="true">*</span>}
                </label>
            )}

            <div className="relative">
                <input
                    ref={ref}
                    id={inputId}
                    disabled={disabled}
                    required={required}
                    aria-invalid={hasError}
                    aria-describedby={describedBy}
                    className={`w-full h-10 px-3.5 text-sm rounded-lg border bg-surface text-foreground transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 placeholder:text-foreground-subtle ${
                        hasError
                            ? "border-danger text-foreground focus:border-danger focus:ring-danger/25"
                            : "border-border hover:border-border-strong focus:border-primary-600 focus:ring-primary-500/20"
                    } disabled:opacity-50 disabled:bg-neutral-100 disabled:cursor-not-allowed ${className}`}
                    {...props}
                />
            </div>

            {hasError && (
                <p id={errorId} className="text-xs font-medium text-danger flex items-center gap-1" role="alert">
                    <svg
                        className="w-3.5 h-3.5 shrink-0"
                        viewBox="0 0 16 16"
                        fill="currentColor"
                        aria-hidden="true"
                    >
                        <path
                            fillRule="evenodd"
                            d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 3.5a.75.75 0 01.75.75v3a.75.75 0 01-1.5 0v-3A.75.75 0 018 4.5zm0 6.5a.875.875 0 100-1.75.875.875 0 000 1.75z"
                            clipRule="evenodd"
                        />
                    </svg>
                    <span>{errorMessage}</span>
                </p>
            )}

            {!hasError && helperText && (
                <p id={helperId} className="text-xs text-foreground-muted">
                    {helperText}
                </p>
            )}
        </div>
    );
});
