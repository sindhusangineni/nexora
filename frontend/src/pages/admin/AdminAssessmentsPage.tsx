import React, { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import {
    AssessmentStatusBadge,
    AssessmentTypeBadge,
    useAssessments,
    type AssessmentStatus,
    type AssessmentType,
} from "@/features/assessment";

export const AdminAssessmentsPage: React.FC = () => {
    const navigate = useNavigate();
    const { data: assessments = [], isLoading, error } = useAssessments();

    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("ALL");
    const [typeFilter, setTypeFilter] = useState<string>("ALL");

    const filteredAssessments = useMemo(() => {
        return assessments.filter((a) => {
            const matchesSearch =
                !search.trim() ||
                a.title.toLowerCase().includes(search.toLowerCase()) ||
                a.description?.toLowerCase().includes(search.toLowerCase());

            const matchesStatus =
                statusFilter === "ALL" || a.status === statusFilter;

            const matchesType = typeFilter === "ALL" || a.type === typeFilter;

            return matchesSearch && matchesStatus && matchesType;
        });
    }, [assessments, search, statusFilter, typeFilter]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                        Assessments
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Create, configure, and publish assessment specifications and test papers.
                    </p>
                </div>
                <Button
                    variant="primary"
                    onClick={() => navigate("/admin/assessments/new")}
                    aria-label="Create Assessment"
                >
                    + Create Assessment
                </Button>
            </div>

            {/* Filter Bar */}
            <div className="p-4 bg-surface border border-border rounded-lg shadow-2xs space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Input
                        placeholder="Search assessments by title..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        aria-label="Search assessments"
                    />

                    <div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            aria-label="Filter by status"
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        >
                            <option value="ALL">All Statuses</option>
                            <option value="DRAFT">Draft</option>
                            <option value="PUBLISHED">Published</option>
                            <option value="ARCHIVED">Archived</option>
                        </select>
                    </div>

                    <div>
                        <select
                            value={typeFilter}
                            onChange={(e) => setTypeFilter(e.target.value)}
                            aria-label="Filter by type"
                            className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        >
                            <option value="ALL">All Types</option>
                            <option value="PRACTICE">Practice</option>
                            <option value="REVISION">Revision</option>
                            <option value="MOCK">Mock</option>
                            <option value="CUSTOM">Custom</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Error State */}
            {error && (
                <div className="p-4 bg-danger-surface border border-danger/20 rounded-md text-sm text-danger">
                    Failed to load assessments. Please refresh the page or try again.
                </div>
            )}

            {/* Loading Skeletons */}
            {isLoading && (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div
                            key={i}
                            className="p-5 bg-surface border border-border rounded-lg space-y-3"
                        >
                            <Skeleton className="h-5 w-1/3" />
                            <Skeleton className="h-4 w-2/3" />
                            <div className="flex space-x-2 pt-2">
                                <Skeleton className="h-6 w-16" />
                                <Skeleton className="h-6 w-20" />
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Assessments List */}
            {!isLoading && filteredAssessments.length === 0 && (
                <EmptyState
                    title="No Assessments Found"
                    description={
                        search || statusFilter !== "ALL" || typeFilter !== "ALL"
                            ? "No assessments match your active filter criteria."
                            : "No assessment specifications exist yet. Create your first assessment to begin."
                    }
                    action={
                        !search && statusFilter === "ALL" && typeFilter === "ALL" ? (
                            <Button
                                variant="primary"
                                onClick={() => navigate("/admin/assessments/new")}
                            >
                                Create First Assessment
                            </Button>
                        ) : undefined
                    }
                />
            )}

            {!isLoading && filteredAssessments.length > 0 && (
                <div className="space-y-3">
                    {filteredAssessments.map((assessment) => {
                        const durationMinutes = Math.round(
                            assessment.duration_seconds / 60,
                        );
                        return (
                            <div
                                key={assessment.id}
                                className="p-5 bg-surface border border-border rounded-lg shadow-2xs hover:border-neutral-300 transition-colors"
                            >
                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                    <div className="space-y-1.5 flex-1">
                                        <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                                            <Link
                                                to={`/admin/assessments/${assessment.id}`}
                                                className="text-base font-semibold text-foreground hover:text-primary transition-colors"
                                            >
                                                {assessment.title}
                                            </Link>
                                            <AssessmentStatusBadge
                                                status={assessment.status as AssessmentStatus}
                                            />
                                            <AssessmentTypeBadge
                                                type={assessment.type as AssessmentType}
                                            />
                                        </div>

                                        {assessment.description && (
                                            <p className="text-xs text-foreground-muted line-clamp-2 max-w-3xl">
                                                {assessment.description}
                                            </p>
                                        )}

                                        <div className="flex items-center space-x-4 text-xs text-foreground-muted flex-wrap gap-y-1 pt-1">
                                            <span>
                                                Duration:{" "}
                                                <strong className="text-neutral-800">
                                                    {durationMinutes} mins
                                                </strong>
                                            </span>
                                            <span>•</span>
                                            <span>
                                                Marking:{" "}
                                                <strong className="text-neutral-800">
                                                    +{assessment.marks_per_question} / -
                                                    {assessment.penalty_per_question}
                                                </strong>
                                            </span>
                                            <span>•</span>
                                            <span>
                                                Updated:{" "}
                                                {new Date(
                                                    assessment.updated_at,
                                                ).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-2 flex-shrink-0">
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            onClick={() =>
                                                navigate(`/admin/assessments/${assessment.id}`)
                                            }
                                        >
                                            View
                                        </Button>

                                        {assessment.status === "DRAFT" && (
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() =>
                                                    navigate(
                                                        `/admin/assessments/${assessment.id}/edit`,
                                                    )
                                                }
                                            >
                                                Edit
                                            </Button>
                                        )}

                                        {assessment.status === "PUBLISHED" && (
                                            <Button
                                                variant="primary"
                                                size="sm"
                                                onClick={() =>
                                                    navigate(
                                                        `/admin/assessments/${assessment.id}`,
                                                    )
                                                }
                                            >
                                                Generate Paper
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};
