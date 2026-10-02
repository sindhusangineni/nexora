import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
}

export function Button({
    children,
    variant = "primary",
    size = "md",
    loading = false,
    disabled = false,
    type = "button",
    ...props
}: ButtonProps) {
    return (
        <button
            type={type}
            data-variant={variant}
            data-size={size}
            {...props}
            disabled={disabled || loading}
            aria-busy={loading ? "true" : props["aria-busy"]}
        >
            {children}
        </button>
    );
}
