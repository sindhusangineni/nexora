import type { HTMLAttributes, CSSProperties } from "react";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
    variant?: "text" | "rectangular" | "circular";
    width?: string | number;
    height?: string | number;
}

export function Skeleton({
    variant = "rectangular",
    width,
    height,
    className = "",
    style,
    ...props
}: SkeletonProps) {
    const variantStyles = {
        text: "h-4 rounded-md w-full",
        rectangular: "rounded-lg",
        circular: "rounded-full",
    };

    const inlineStyles: CSSProperties = {
        width,
        height,
        ...style,
    };

    return (
        <div
            className={`animate-pulse bg-neutral-200/80 ${variantStyles[variant]} ${className}`}
            style={inlineStyles}
            aria-hidden="true"
            {...props}
        />
    );
}
