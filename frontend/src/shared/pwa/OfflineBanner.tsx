import React from "react";
import { useNetworkStatus } from "./useNetworkStatus";

export const OfflineBanner: React.FC = () => {
    const { isOnline } = useNetworkStatus();

    if (isOnline) return null;

    return (
        <div
            role="status"
            aria-live="polite"
            className="sticky top-0 z-50 bg-amber-600 text-white text-xs sm:text-sm font-medium px-4 py-2.5 flex items-center justify-center space-x-2 shadow-sm animate-in fade-in duration-200"
        >
            <svg
                className="w-4 h-4 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L12 12m6.364-6.364L12 12m0 0L5.636 5.636M12 12l-6.364 6.364M3 3l18 18"
                />
            </svg>
            <span>
                <strong>You appear to be offline.</strong> Protected assessment operations require an active network connection.
            </span>
        </div>
    );
};
