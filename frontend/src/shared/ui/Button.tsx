import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
}

const baseStyles =
    "inline-flex items-center justify-center font-medium cursor-pointer transition-colors duration-150 select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none";

const variantStyles: Record<ButtonVariant, string> = {
    primary:
        "bg-primary-600 text-surface hover:bg-primary-700 active:bg-primary-800 focus-visible:ring-primary-500 shadow-xs",
    secondary:
        "bg-surface text-foreground border border-border hover:bg-surface-muted hover:border-border-strong active:bg-neutral-200 focus-visible:ring-primary-500 shadow-xs",
    danger:
        "bg-danger text-surface hover:bg-red-700 active:bg-red-800 focus-visible:ring-danger shadow-xs",
    ghost:
        "bg-transparent text-foreground border border-transparent hover:bg-surface-muted hover:text-foreground active:bg-neutral-200 focus-visible:ring-primary-500",
};

const sizeStyles: Record<ButtonSize, string> = {
    sm: "h-8 px-3 text-xs gap-1.5 rounded-sm",
    md: "h-9 px-4 text-sm gap-2 rounded-md",
    lg: "h-10 px-5 text-base gap-2.5 rounded-lg",
};

function LoadingSpinner() {
    return (
        <svg
            className="h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
        >
            <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
            />
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
        </svg>
    );
}

export function Button({
    children,
    variant = "primary",
    size = "md",
    loading = false,
    disabled = false,
    type = "button",
    className,
    ...props
}: ButtonProps) {
    const combinedClassName = [
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <button
            type={type}
            data-variant={variant}
            data-size={size}
            className={combinedClassName}
            disabled={disabled || loading}
            aria-busy={loading ? "true" : props["aria-busy"]}
            {...props}
        >
            {loading && <LoadingSpinner />}
            {children}
        </button>
    );
}
