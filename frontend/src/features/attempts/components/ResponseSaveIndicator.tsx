import React from "react";
import { CheckIcon, AlertCircleIcon, LoaderIcon } from "./Icons";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

interface ResponseSaveIndicatorProps {
    status: SaveStatus;
    errorMessage?: string;
    onRetry?: () => void;
    className?: string;
}

export const ResponseSaveIndicator: React.FC<ResponseSaveIndicatorProps> = ({
    status,
    errorMessage,
    onRetry,
    className = "",
}) => {
    if (status === "idle") {
        return null;
    }

    if (status === "saving") {
        return (
            <div
                className={`inline-flex items-center space-x-1.5 text-xs text-neutral-500 font-medium ${className}`}
                aria-live="polite"
            >
                <LoaderIcon className="w-3.5 h-3.5 animate-spin text-primary" />
                <span>Saving response...</span>
            </div>
        );
    }

    if (status === "saved") {
        return (
            <div
                className={`inline-flex items-center space-x-1.5 text-xs text-emerald-600 font-medium ${className}`}
                aria-live="polite"
            >
                <CheckIcon className="w-3.5 h-3.5 text-emerald-500" />
                <span>Saved on server</span>
            </div>
        );
    }

    if (status === "error") {
        return (
            <div
                className={`inline-flex items-center space-x-2 text-xs text-red-600 font-medium ${className}`}
                aria-live="assertive"
            >
                <AlertCircleIcon className="w-3.5 h-3.5 text-red-500 shrink-0" />
                <span>{errorMessage || "Failed to save answer."}</span>
                {onRetry && (
                    <button
                        type="button"
                        onClick={onRetry}
                        className="underline hover:text-red-700 font-semibold cursor-pointer"
                    >
                        Retry
                    </button>
                )}
            </div>
        );
    }

    return null;
};
