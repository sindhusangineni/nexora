import type { HTMLAttributes, ReactNode } from "react";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
    interactive?: boolean;
    children: ReactNode;
}

export function Card({ interactive = false, className = "", children, ...props }: CardProps) {
    return (
        <div
            className={`bg-surface rounded-xl border border-border shadow-xs transition-all duration-200 ${
                interactive
                    ? "hover:border-neutral-300 hover:shadow-sm hover:-translate-y-0.5 cursor-pointer"
                    : ""
            } ${className}`}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({
    className = "",
    children,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`p-6 pb-3 space-y-1.5 ${className}`} {...props}>
            {children}
        </div>
    );
}

export function CardTitle({
    className = "",
    children,
    as: Component = "h3",
    ...props
}: HTMLAttributes<HTMLHeadingElement> & { as?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" }) {
    return (
        <Component
            className={`text-base font-semibold text-foreground tracking-tight ${className}`}
            {...props}
        >
            {children}
        </Component>
    );
}

export function CardDescription({
    className = "",
    children,
    ...props
}: HTMLAttributes<HTMLParagraphElement>) {
    return (
        <p className={`text-sm text-foreground-muted leading-relaxed ${className}`} {...props}>
            {children}
        </p>
    );
}

export function CardContent({
    className = "",
    children,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`p-6 pt-0 ${className}`} {...props}>
            {children}
        </div>
    );
}

export function CardFooter({
    className = "",
    children,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`p-6 pt-0 flex items-center justify-between gap-4 ${className}`} {...props}>
            {children}
        </div>
    );
}
