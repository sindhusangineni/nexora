import React from "react";

interface AttemptProgressProps {
    answeredCount: number;
    totalCount: number;
    className?: string;
}

export const AttemptProgress: React.FC<AttemptProgressProps> = ({
    answeredCount,
    totalCount,
    className = "",
}) => {
    const percentage = totalCount > 0 ? Math.round((answeredCount / totalCount) * 100) : 0;

    return (
        <div className={`space-y-1.5 ${className}`}>
            <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-neutral-800">
                    {answeredCount} of {totalCount} Answered
                </span>
                <span className="text-foreground-muted font-medium font-mono">
                    {percentage}%
                </span>
            </div>
            <div className="w-full h-1.5 bg-neutral-100 rounded-full overflow-hidden border border-neutral-200">
                <div
                    className="h-full bg-primary transition-all duration-300 ease-out rounded-full"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
};
