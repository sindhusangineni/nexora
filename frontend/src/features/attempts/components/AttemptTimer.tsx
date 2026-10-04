import React, { useEffect, useState, useRef } from "react";
import { ClockIcon, AlertTriangleIcon } from "./Icons";

interface AttemptTimerProps {
    expiresAt: string;
    onExpire?: () => void;
    className?: string;
    isPaused?: boolean;
}

function getSecondsRemaining(expiresAt: string): number {
    const expiryTime = new Date(expiresAt).getTime();
    const now = Date.now();
    return Math.max(0, Math.floor((expiryTime - now) / 1000));
}

export const AttemptTimer: React.FC<AttemptTimerProps> = ({
    expiresAt,
    onExpire,
    className = "",
    isPaused = false,
}) => {
    const [secondsLeft, setSecondsLeft] = useState<number>(() => getSecondsRemaining(expiresAt));
    const expiredRef = useRef(false);

    useEffect(() => {
        if (isPaused) return;

        const updateTimer = () => {
            const remaining = getSecondsRemaining(expiresAt);
            setSecondsLeft(remaining);

            if (remaining <= 0 && !expiredRef.current) {
                expiredRef.current = true;
                onExpire?.();
            }
        };

        updateTimer();
        const interval = setInterval(updateTimer, 1000);

        return () => clearInterval(interval);
    }, [expiresAt, isPaused, onExpire]);

    const hours = Math.floor(secondsLeft / 3600);
    const minutes = Math.floor((secondsLeft % 3600) / 60);
    const seconds = secondsLeft % 60;

    const formattedTime = [
        hours > 0 ? String(hours).padStart(2, "0") : null,
        String(minutes).padStart(2, "0"),
        String(seconds).padStart(2, "0"),
    ]
        .filter(Boolean)
        .join(":");

    const isUrgent = secondsLeft <= 300 && secondsLeft > 0; // Under 5 minutes
    const isCritical = secondsLeft <= 60 && secondsLeft > 0; // Under 1 minute
    const isExpired = secondsLeft === 0;

    return (
        <div
            className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg border font-mono text-xs font-semibold tracking-wider transition-colors ${
                isExpired
                    ? "bg-red-50 text-red-700 border-red-200"
                    : isCritical
                    ? "bg-red-50 text-red-600 border-red-300 animate-pulse"
                    : isUrgent
                    ? "bg-amber-50 text-amber-700 border-amber-300"
                    : "bg-surface text-neutral-800 border-border"
            } ${className}`}
            role="timer"
            aria-live="polite"
            aria-label={`Time remaining: ${formattedTime}`}
        >
            {isUrgent || isCritical || isExpired ? (
                <AlertTriangleIcon className="w-3.5 h-3.5 text-current shrink-0" />
            ) : (
                <ClockIcon className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
            )}
            <span>
                {isExpired ? "Time Expired" : formattedTime}
            </span>
        </div>
    );
};
