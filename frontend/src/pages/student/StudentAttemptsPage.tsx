import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import {
    HistoryIcon,
    PlayIcon,
    CheckIcon,
    ArrowRightIcon,
    AlertCircleIcon,
} from "@/features/attempts/components/Icons";
import { useAttemptHistory } from "@/features/attempts/hooks/useAttempts";
import type { AttemptHistoryItem, AttemptStatus } from "@/features/attempts/types/attempt.types";

export const StudentAttemptsPage: React.FC = () => {
    const navigate = useNavigate();
    const [lookupId, setLookupId] = useState("");
    const [statusFilter, setStatusFilter] = useState<AttemptStatus | "">("");
    const [page, setPage] = useState(1);

    const {
        data: historyData,
        isLoading,
        isError,
        error,
        refetch,
    } = useAttemptHistory({
        status: statusFilter ? statusFilter : undefined,
        page,
        page_size: 20,
    });

    const handleLookup = (e: React.FormEvent) => {
        e.preventDefault();
        const trimmed = lookupId.trim();
        if (trimmed) {
            navigate(`/student/attempts/${trimmed}`);
        }
    };

    const handleFilterChange = (newStatus: AttemptStatus | "") => {
        setStatusFilter(newStatus);
        setPage(1);
    };

    const renderStatusBadge = (status: AttemptStatus) => {
        switch (status) {
            case "IN_PROGRESS":
                return <Badge variant="info">In Progress</Badge>;
            case "SUBMITTED":
                return <Badge variant="warning">Submitted</Badge>;
            case "EVALUATED":
                return <Badge variant="success">Evaluated</Badge>;
            case "CANCELLED":
                return <Badge variant="danger">Cancelled</Badge>;
            default:
                return <Badge variant="default">{status}</Badge>;
        }
    };

    const renderResultSummary = (item: AttemptHistoryItem) => {
        if (item.result_status === "FINAL" && item.score !== null) {
            return (
                <div className="flex flex-col">
                    <span className="font-semibold text-foreground text-xs sm:text-sm">
                        {item.score} / {item.maximum_score}
                    </span>
                    <span className="text-[11px] text-foreground-muted">
                        {item.percentage}%
                    </span>
                </div>
            );
        }
        if (item.result_status === "PENDING") {
            return <Badge variant="warning">Pending Evaluation</Badge>;
        }
        if (item.result_status === "VOID") {
            return <Badge variant="danger">Void</Badge>;
        }
        return <span className="text-foreground-muted text-xs">—</span>;
    };

    const renderAction = (item: AttemptHistoryItem) => {
        if (item.status === "IN_PROGRESS") {
            return (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate(`/student/attempts/${item.id}`)}
                >
                    Continue Test
                </Button>
            );
        }
        if (item.status === "SUBMITTED" || item.status === "EVALUATED") {
            return (
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/student/attempts/${item.id}/result`)}
                >
                    {item.result_status === "PENDING" ? "View Status" : "View Result"}
                </Button>
            );
        }
        return (
            <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate(`/student/attempts/${item.id}`)}
            >
                Details
            </Button>
        );
    };

    const totalPages = historyData ? Math.ceil(historyData.count / 20) : 1;

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">
                        My Attempts
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Track your assessment sessions, active attempts, and scorecards.
                    </p>
                </div>

                <div className="flex items-center space-x-3">
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => navigate("/student/assessments")}
                    >
                        Browse Assessments
                    </Button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center space-x-2">
                    <label htmlFor="status-filter" className="text-xs font-medium text-foreground-muted">
                        Filter by Status:
                    </label>
                    <select
                        id="status-filter"
                        value={statusFilter}
                        onChange={(e) => handleFilterChange(e.target.value as AttemptStatus | "")}
                        className="text-xs bg-surface border border-border rounded-md px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                        <option value="">All Statuses</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="SUBMITTED">Submitted</option>
                        <option value="EVALUATED">Evaluated</option>
                        <option value="CANCELLED">Cancelled</option>
                    </select>
                </div>

                {historyData && (
                    <span className="text-xs text-foreground-muted">
                        Showing {historyData.results.length} of {historyData.count} attempts
                    </span>
                )}
            </div>

            {/* Attempt History List */}
            {isLoading ? (
                <Card className="p-6 space-y-4 border-border">
                    <Skeleton className="h-6 w-1/4" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                </Card>
            ) : isError ? (
                <Card className="p-6 border-red-200 bg-red-50/30 text-center space-y-3">
                    <div className="flex items-center justify-center space-x-2 text-red-600">
                        <AlertCircleIcon className="w-5 h-5" />
                        <span className="text-sm font-semibold">Failed to load attempt history</span>
                    </div>
                    <p className="text-xs text-foreground-muted">
                        {error instanceof Error ? error.message : "Unable to retrieve attempts"}
                    </p>
                    <Button variant="secondary" size="sm" onClick={() => refetch()}>
                        Retry
                    </Button>
                </Card>
            ) : historyData && historyData.results.length > 0 ? (
                <div className="space-y-4">
                    {/* Mobile Stacked Cards (< sm) */}
                    <div className="block sm:hidden space-y-3">
                        {historyData.results.map((item) => (
                            <Card key={item.id} className="p-4 border-border bg-surface space-y-3 shadow-2xs">
                                <div className="flex items-center justify-between gap-2">
                                    <div>
                                        <div className="font-semibold text-foreground text-sm">
                                            Attempt #{item.attempt_number}
                                        </div>
                                        <div className="text-[11px] text-foreground-muted font-mono mt-0.5">
                                            Paper: {item.assessment_paper_id.slice(0, 8)}...
                                        </div>
                                    </div>
                                    <div>
                                        {renderStatusBadge(item.status)}
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-xs border-y border-border/60 py-2.5">
                                    <div>
                                        <span className="text-[10px] uppercase font-semibold text-foreground-muted block mb-0.5">
                                            Timeline
                                        </span>
                                        <div className="text-foreground">
                                            {new Date(item.started_at).toLocaleDateString()}
                                        </div>
                                        <div className="text-foreground-muted text-[11px]">
                                            {new Date(item.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>

                                    <div>
                                        <span className="text-[10px] uppercase font-semibold text-foreground-muted block mb-0.5">
                                            Score / Result
                                        </span>
                                        {renderResultSummary(item)}
                                    </div>
                                </div>

                                <div className="pt-1 flex items-center justify-end">
                                    {renderAction(item)}
                                </div>
                            </Card>
                        ))}
                    </div>

                    {/* Desktop & Tablet Table (sm and up) */}
                    <Card className="hidden sm:block overflow-hidden border-border bg-surface shadow-xs">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs sm:text-sm">
                                <thead className="bg-surface-muted/50 border-b border-border text-foreground-muted text-[11px] uppercase font-semibold tracking-wider">
                                    <tr>
                                        <th className="px-4 py-3">Attempt</th>
                                        <th className="px-4 py-3">Status</th>
                                        <th className="px-4 py-3">Timeline</th>
                                        <th className="px-4 py-3">Score / Result</th>
                                        <th className="px-4 py-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {historyData.results.map((item) => (
                                        <tr key={item.id} className="hover:bg-surface-muted/30 transition-colors">
                                            <td className="px-4 py-3.5 align-middle">
                                                <div className="font-semibold text-foreground">
                                                    Attempt #{item.attempt_number}
                                                </div>
                                                <div className="text-[11px] text-foreground-muted font-mono mt-0.5">
                                                    Paper: {item.assessment_paper_id.slice(0, 8)}...
                                                </div>
                                            </td>
                                            <td className="px-4 py-3.5 align-middle">
                                                {renderStatusBadge(item.status)}
                                            </td>
                                            <td className="px-4 py-3.5 align-middle text-xs">
                                                <div className="text-foreground">
                                                    Started: {new Date(item.started_at).toLocaleString()}
                                                </div>
                                                {item.submitted_at ? (
                                                    <div className="text-foreground-muted text-[11px] mt-0.5">
                                                        Submitted: {new Date(item.submitted_at).toLocaleString()}
                                                    </div>
                                                ) : (
                                                    <div className="text-foreground-muted text-[11px] mt-0.5">
                                                        Expires: {new Date(item.expires_at).toLocaleString()}
                                                    </div>
                                                )}
                                            </td>
                                            <td className="px-4 py-3.5 align-middle">
                                                {renderResultSummary(item)}
                                            </td>
                                            <td className="px-4 py-3.5 align-middle text-right">
                                                {renderAction(item)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </Card>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between border-t border-border pt-4">
                            <Button
                                variant="secondary"
                                size="sm"
                                disabled={page <= 1}
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                            >
                                Previous
                            </Button>
                            <span className="text-xs text-foreground-muted">
                                Page {page} of {totalPages}
                            </span>
                            <Button
                                variant="secondary"
                                size="sm"
                                disabled={page >= totalPages}
                                onClick={() => setPage((p) => p + 1)}
                            >
                                Next
                            </Button>
                        </div>
                    )}
                </div>
            ) : (
                <EmptyState
                    title={statusFilter ? "No matching attempts" : "No Attempts Yet"}
                    description={
                        statusFilter
                            ? "No assessment sessions match the selected filter."
                            : "Your attempt history will appear here once you take your first test."
                    }
                    action={
                        statusFilter ? (
                            <Button variant="secondary" size="sm" onClick={() => handleFilterChange("")}>
                                Clear Filter
                            </Button>
                        ) : (
                            <Button
                                variant="primary"
                                size="sm"
                                onClick={() => navigate("/student/assessments")}
                            >
                                Browse Available Assessments
                            </Button>
                        )
                    }
                />
            )}

            {/* Quick Resume by ID Card */}
            <Card className="p-6 bg-surface border-border space-y-4">
                <div className="flex items-center space-x-2">
                    <HistoryIcon className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground tracking-tight">
                        Direct Attempt Lookup
                    </h3>
                </div>
                <p className="text-xs text-foreground-muted">
                    If you have a specific Attempt UUID from another session or device, enter it below to jump directly to it.
                </p>
                <form onSubmit={handleLookup} className="flex flex-col sm:flex-row gap-3">
                    <Input
                        type="text"
                        placeholder="Enter Attempt UUID..."
                        value={lookupId}
                        onChange={(e) => setLookupId(e.target.value)}
                        className="flex-1 text-xs"
                    />
                    <Button
                        type="submit"
                        variant="secondary"
                        size="sm"
                        disabled={!lookupId.trim()}
                    >
                        Go to Attempt
                    </Button>
                </form>
            </Card>

            {/* Attempts Overview Banner */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-5 flex items-start space-x-4 border-border">
                    <div className="p-2.5 rounded-lg bg-primary-50 text-primary-700 shrink-0">
                        <PlayIcon className="w-5 h-5" />
                    </div>
                    <div>
                        <h4 className="text-sm font-semibold text-foreground">
                            Take New Assessment
                        </h4>
                        <p className="text-xs text-foreground-muted mt-1 leading-relaxed">
                            Select from published practice tests and mock papers in the student catalog.
                        </p>
                        <Link
                            to="/student/assessments"
                            className="inline-flex items-center space-x-1 text-xs text-primary font-semibold hover:underline mt-2.5"
                        >
                            <span>Explore tests</span>
                            <ArrowRightIcon className="w-3.5 h-3.5" />
                        </Link>
                    </div>
                </Card>

                <Card className="p-5 flex items-start space-x-4 border-border">
                    <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-700 shrink-0">
                        <CheckIcon className="w-5 h-5" />
                    </div>
                    <div>
                        <h4 className="text-sm font-semibold text-foreground">
                            Synchronous Grading
                        </h4>
                        <p className="text-xs text-foreground-muted mt-1 leading-relaxed">
                            Objective tests are scored instantly upon submission with detailed section marks.
                        </p>
                        <span className="inline-block text-[11px] text-emerald-800 font-medium mt-2.5">
                            Automated & Transparent
                        </span>
                    </div>
                </Card>
            </div>
        </div>
    );
};
