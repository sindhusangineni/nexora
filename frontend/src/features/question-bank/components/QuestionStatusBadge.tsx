import { Badge, type BadgeVariant } from "@/shared/ui/Badge";
import type { QuestionStatus } from "../types/questionBank.types";

export interface QuestionStatusBadgeProps {
    status: QuestionStatus;
    size?: "sm" | "md";
    className?: string;
}

export function QuestionStatusBadge({
    status,
    size = "sm",
    className = "",
}: QuestionStatusBadgeProps) {
    const config: Record<
        QuestionStatus,
        { label: string; variant: BadgeVariant }
    > = {
        DRAFT: { label: "Draft", variant: "default" },
        REVIEW: { label: "In Review", variant: "warning" },
        APPROVED: { label: "Approved", variant: "info" },
        PUBLISHED: { label: "Published", variant: "success" },
        ARCHIVED: { label: "Archived", variant: "outline" },
    };

    const item = config[status] || { label: status, variant: "default" };

    return (
        <Badge variant={item.variant} size={size} className={className}>
            {item.label}
        </Badge>
    );
}
