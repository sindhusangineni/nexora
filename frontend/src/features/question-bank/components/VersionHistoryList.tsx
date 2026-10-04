import { Badge } from "@/shared/ui/Badge";
import { QuestionStatusBadge } from "./QuestionStatusBadge";
import type { QuestionVersionAdminResponse } from "../types/questionBank.types";

export interface VersionHistoryListProps {
    versions: QuestionVersionAdminResponse[];
    selectedVersionId: string;
    publishedVersionId?: string;
    onSelectVersion: (version: QuestionVersionAdminResponse) => void;
    className?: string;
}

export function VersionHistoryList({
    versions,
    selectedVersionId,
    publishedVersionId,
    onSelectVersion,
    className = "",
}: VersionHistoryListProps) {
    const sortedVersions = [...versions].sort(
        (a, b) => b.version_number - a.version_number,
    );

    return (
        <div className={`space-y-3 ${className}`}>
            <div className="flex items-center justify-between pb-2 border-b border-border">
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-500">
                    Version History ({versions.length})
                </h4>
            </div>

            <div className="space-y-2">
                {sortedVersions.map((version) => {
                    const isSelected = version.id === selectedVersionId;
                    const isPublished = version.id === publishedVersionId;
                    const formattedDate = new Date(version.created_at).toLocaleDateString(
                        undefined,
                        { year: "numeric", month: "short", day: "numeric" },
                    );

                    return (
                        <div
                            key={version.id}
                            onClick={() => onSelectVersion(version)}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                    e.preventDefault();
                                    onSelectVersion(version);
                                }
                            }}
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${
                                isSelected
                                    ? "bg-primary-50/60 border-primary-300 ring-1 ring-primary-300"
                                    : "bg-surface border-border hover:border-neutral-300 hover:bg-surface-muted"
                            }`}
                        >
                            <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2">
                                    <span className="font-mono font-bold text-sm text-foreground">
                                        v{version.version_number}
                                    </span>
                                    <QuestionStatusBadge status={version.status} size="sm" />
                                </div>
                                {isPublished && (
                                    <Badge variant="success" size="sm">
                                        Live
                                    </Badge>
                                )}
                            </div>

                            <div className="mt-2 flex items-center justify-between text-[11px] text-foreground-muted">
                                <span>{formattedDate}</span>
                                {isSelected ? (
                                    <span className="font-semibold text-primary-600">
                                        Active View
                                    </span>
                                ) : (
                                    <span className="text-neutral-400">Inspect</span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
