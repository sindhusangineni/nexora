import { Link } from "react-router-dom";

export interface BrandLogoProps {
    size?: "sm" | "md" | "lg";
    showWordmark?: boolean;
    subtitle?: string;
    className?: string;
    to?: string;
}

export function BrandLogo({
    size = "md",
    showWordmark = true,
    subtitle,
    className = "",
    to,
}: BrandLogoProps) {
    const emblemSizes = {
        sm: "w-7 h-7",
        md: "w-8 h-8",
        lg: "w-10 h-10",
    };

    const textSizes = {
        sm: "text-lg",
        md: "text-xl",
        lg: "text-2xl",
    };

    const content = (
        <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
            {/* Nexora Emblem: Precision Layered Compass / Diamond of Mastery */}
            <div
                className={`${emblemSizes[size]} relative flex items-center justify-center rounded-lg bg-primary-900 text-white shadow-xs overflow-hidden shrink-0`}
                aria-hidden="true"
            >
                <svg
                    viewBox="0 0 32 32"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-full h-full p-1"
                >
                    {/* Background subtle geometric grid line */}
                    <path
                        d="M16 4 L28 16 L16 28 L4 16 Z"
                        stroke="rgba(255, 255, 255, 0.2)"
                        strokeWidth="1.5"
                    />
                    {/* Inner core node - academic knowledge nexus */}
                    <circle cx="16" cy="16" r="3" fill="#60a5fa" />
                    {/* Stylized 'N' intersecting dynamic path */}
                    <path
                        d="M10 21 V11 L22 21 V11"
                        stroke="#ffffff"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </svg>
            </div>

            {showWordmark && (
                <div className="flex flex-col">
                    <span
                        className={`${textSizes[size]} font-bold tracking-tight text-neutral-900 leading-none`}
                    >
                        Nexora
                    </span>
                    {subtitle && (
                        <span className="text-[10px] uppercase font-semibold tracking-wider text-neutral-500 mt-0.5">
                            {subtitle}
                        </span>
                    )}
                </div>
            )}
        </div>
    );

    if (to) {
        return (
            <Link
                to={to}
                className="inline-flex focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-md"
                aria-label="Nexora Home"
            >
                {content}
            </Link>
        );
    }

    return content;
}
