import type { HTMLAttributes, ReactNode } from "react";

export type BadgeVariant =
    | "default"
    | "primary"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "outline";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    variant?: BadgeVariant;
    size?: "sm" | "md";
    children: ReactNode;
}

export function Badge({
    variant = "default",
    size = "sm",
    className = "",
    children,
    ...props
}: BadgeProps) {
    const variantStyles: Record<BadgeVariant, string> = {
        default: "bg-neutral-100 text-neutral-700 border-neutral-200",
        primary: "bg-primary-50 text-primary-700 border-primary-200",
        success: "bg-emerald-50 text-emerald-700 border-emerald-200",
        warning: "bg-amber-50 text-amber-700 border-amber-200",
        danger: "bg-red-50 text-red-700 border-red-200",
        info: "bg-sky-50 text-sky-700 border-sky-200",
        outline: "bg-transparent text-neutral-700 border-neutral-300",
    };

    const sizeStyles = {
        sm: "text-xs px-2 py-0.5 font-medium",
        md: "text-xs px-2.5 py-1 font-semibold",
    };

    return (
        <span
            className={`inline-flex items-center rounded-full border tracking-wide select-none transition-colors ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
            {...props}
        >
            {children}
        </span>
    );
}
