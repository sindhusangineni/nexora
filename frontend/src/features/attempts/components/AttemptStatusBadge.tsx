import React from "react";
import { Badge } from "@/shared/ui/Badge";
import type { AttemptStatus, AttemptResultStatus } from "../types/attempt.types";

interface AttemptStatusBadgeProps {
    status: AttemptStatus;
    className?: string;
}

export const AttemptStatusBadge: React.FC<AttemptStatusBadgeProps> = ({
    status,
    className,
}) => {
    switch (status) {
        case "IN_PROGRESS":
            return (
                <Badge variant="warning" size="sm" className={className}>
                    In Progress
                </Badge>
            );
        case "SUBMITTED":
            return (
                <Badge variant="info" size="sm" className={className}>
                    Submitted
                </Badge>
            );
        case "EVALUATED":
            return (
                <Badge variant="success" size="sm" className={className}>
                    Evaluated
                </Badge>
            );
        case "CANCELLED":
            return (
                <Badge variant="danger" size="sm" className={className}>
                    Cancelled
                </Badge>
            );
        default:
            return (
                <Badge variant="default" size="sm" className={className}>
                    {status}
                </Badge>
            );
    }
};

interface AttemptResultStatusBadgeProps {
    status: AttemptResultStatus;
    className?: string;
}

export const AttemptResultStatusBadge: React.FC<AttemptResultStatusBadgeProps> = ({
    status,
    className,
}) => {
    switch (status) {
        case "FINAL":
            return (
                <Badge variant="success" size="sm" className={className}>
                    Final Result
                </Badge>
            );
        case "PENDING":
            return (
                <Badge variant="warning" size="sm" className={className}>
                    Evaluation Pending
                </Badge>
            );
        case "VOID":
            return (
                <Badge variant="danger" size="sm" className={className}>
                    Void
                </Badge>
            );
        default:
            return (
                <Badge variant="default" size="sm" className={className}>
                    {status}
                </Badge>
            );
    }
};
