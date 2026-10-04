import React from "react";
import { Badge } from "@/shared/ui/Badge";
import type { AssessmentStatus, AssessmentType } from "../types/assessment.types";

interface AssessmentStatusBadgeProps {
    status: AssessmentStatus;
    className?: string;
}

export const AssessmentStatusBadge: React.FC<AssessmentStatusBadgeProps> = ({
    status,
    className,
}) => {
    switch (status) {
        case "PUBLISHED":
            return (
                <Badge variant="success" size="sm" className={className}>
                    Published
                </Badge>
            );
        case "ARCHIVED":
            return (
                <Badge variant="default" size="sm" className={className}>
                    Archived
                </Badge>
            );
        case "DRAFT":
        default:
            return (
                <Badge variant="warning" size="sm" className={className}>
                    Draft
                </Badge>
            );
    }
};

interface AssessmentTypeBadgeProps {
    type: AssessmentType;
    className?: string;
}

export const AssessmentTypeBadge: React.FC<AssessmentTypeBadgeProps> = ({
    type,
    className,
}) => {
    switch (type) {
        case "MOCK":
            return (
                <Badge variant="info" size="sm" className={className}>
                    Mock
                </Badge>
            );
        case "REVISION":
            return (
                <Badge variant="default" size="sm" className={className}>
                    Revision
                </Badge>
            );
        case "CUSTOM":
            return (
                <Badge variant="warning" size="sm" className={className}>
                    Custom
                </Badge>
            );
        case "PRACTICE":
        default:
            return (
                <Badge variant="default" size="sm" className={className}>
                    Practice
                </Badge>
            );
    }
};
