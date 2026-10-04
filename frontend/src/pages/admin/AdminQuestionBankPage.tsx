import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import {
    QuestionStatusBadge,
    useQuestions,
    type Difficulty,
    type QuestionFilterParams,
    type QuestionStatus,
    type QuestionType,
} from "@/features/question-bank";

export function AdminQuestionBankPage() {
    const navigate = useNavigate();

    // Filters state
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState<QuestionStatus | "">("");
    const [typeFilter, setTypeFilter] = useState<QuestionType | "">("");
    const [difficultyFilter, setDifficultyFilter] = useState<Difficulty | "">("");
    const [page, setPage] = useState(1);

    const queryParams: QuestionFilterParams = {
        page,
        page_size: 15,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        question_type: typeFilter || undefined,
        difficulty: difficultyFilter || undefined,
    };

    const { data, isLoading, isError, refetch } = useQuestions(queryParams);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
    };

    const handleResetFilters = () => {
        setSearch("");
        setStatusFilter("");
        setTypeFilter("");
        setDifficultyFilter("");
        setPage(1);
    };

    const statusTabs: Array<{ label: string; value: QuestionStatus | "" }> = [
        { label: "All Questions", value: "" },
        { label: "Draft", value: "DRAFT" },
        { label: "In Review", value: "REVIEW" },
        { label: "Approved", value: "APPROVED" },
        { label: "Published", value: "PUBLISHED" },
        { label: "Archived", value: "ARCHIVED" },
    ];

    const totalCount = data?.count ?? 0;
    const totalPages = Math.ceil(totalCount / 15) || 1;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Badge variant="default" size="sm">
                            Authoring & Versioning
                        </Badge>
                        <span className="text-xs text-foreground-muted">Content Repository</span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        Question Bank
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Manage, review, version, and publish standardized assessment questions.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <Link to="/admin/question-bank/import">
                        <Button variant="secondary" size="md">
                            Bulk Import (CSV)
                        </Button>
                    </Link>
                    <Link to="/admin/question-bank/questions/new">
                        <Button variant="primary" size="md">
                            + Create Question
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Status Tabs Filter */}
            <div className="flex overflow-x-auto gap-1 border-b border-border pb-1">
                {statusTabs.map((tab) => (
                    <button
                        key={tab.label}
                        type="button"
                        onClick={() => {
                            setStatusFilter(tab.value);
                            setPage(1);
                        }}
                        className={`px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-colors ${
                            statusFilter === tab.value
                                ? "bg-neutral-900 text-white shadow-xs"
                                : "text-foreground-muted hover:text-foreground hover:bg-neutral-100"
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Filters Bar */}
            <Card>
                <CardContent className="p-4">
                    <form
                        onSubmit={handleSearchSubmit}
                        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-center"
                    >
                        {/* Search Input */}
                        <div className="lg:col-span-2">
                            <input
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Search questions by text or explanation..."
                                aria-label="Search questions"
                                className="w-full h-10 px-3.5 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600"
                            />
                        </div>

                        {/* Question Type Filter */}
                        <div>
                            <select
                                value={typeFilter}
                                onChange={(e) => {
                                    setTypeFilter(e.target.value as QuestionType | "");
                                    setPage(1);
                                }}
                                aria-label="Filter by question type"
                                className="w-full h-10 px-3 text-xs rounded-lg border border-border bg-surface text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600"
                            >
                                <option value="">All Question Types</option>
                                <option value="MCQ">Multiple Choice (Single)</option>
                                <option value="MULTIPLE_SELECT">Multiple Select</option>
                                <option value="TRUE_FALSE">True / False</option>
                                <option value="ASSERTION_REASON">Assertion & Reason</option>
                                <option value="MATCH_FOLLOWING">Match the Following</option>
                                <option value="DESCRIPTIVE">Descriptive</option>
                            </select>
                        </div>

                        {/* Difficulty Filter */}
                        <div>
                            <select
                                value={difficultyFilter}
                                onChange={(e) => {
                                    setDifficultyFilter(e.target.value as Difficulty | "");
                                    setPage(1);
                                }}
                                aria-label="Filter by difficulty"
                                className="w-full h-10 px-3 text-xs rounded-lg border border-border bg-surface text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600"
                            >
                                <option value="">All Difficulties</option>
                                <option value="EASY">Easy</option>
                                <option value="MEDIUM">Medium</option>
                                <option value="HARD">Hard</option>
                            </select>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center gap-2">
                            <Button type="submit" variant="secondary" size="md" className="flex-1">
                                Search
                            </Button>
                            {(search || statusFilter || typeFilter || difficultyFilter) && (
                                <button
                                    type="button"
                                    onClick={handleResetFilters}
                                    title="Reset filters"
                                    aria-label="Reset all filters"
                                    className="p-2.5 rounded-lg border border-border text-foreground-muted hover:text-foreground hover:bg-neutral-100 text-xs"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* Questions Table */}
            <Card className="overflow-hidden">
                <CardHeader className="py-3 px-6 border-b border-border bg-surface-muted/30">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-semibold">
                            Questions ({totalCount})
                        </CardTitle>
                        <span className="text-xs text-foreground-muted">
                            Page {page} of {totalPages}
                        </span>
                    </div>
                </CardHeader>

                {isLoading && (
                    <div className="p-6 space-y-4">
                        <Skeleton height={40} className="w-full" />
                        <Skeleton height={40} className="w-full" />
                        <Skeleton height={40} className="w-full" />
                    </div>
                )}

                {isError && (
                    <div className="p-8 text-center space-y-3">
                        <p className="text-sm font-medium text-danger">
                            Failed to load question records from the server.
                        </p>
                        <Button variant="secondary" size="sm" onClick={() => refetch()}>
                            Retry
                        </Button>
                    </div>
                )}

                {!isLoading && !isError && (!data?.results || data.results.length === 0) && (
                    <div className="p-8">
                        <EmptyState
                            title="No questions found"
                            description={
                                search || statusFilter || typeFilter || difficultyFilter
                                    ? "No questions match your selected filter criteria. Try resetting filters."
                                    : "Start building your assessment repository by authoring your first question."
                            }
                            action={
                                <Link to="/admin/question-bank/questions/new">
                                    <Button variant="primary" size="sm">
                                        + Create Question
                                    </Button>
                                </Link>
                            }
                        />
                    </div>
                )}

                {!isLoading && !isError && data?.results && data.results.length > 0 && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse" aria-label="Questions table">
                            <thead>
                                <tr className="border-b border-border bg-surface-muted/20 text-[11px] font-bold uppercase tracking-wider text-neutral-500">
                                    <th className="py-3 px-6">Question Stem</th>
                                    <th className="py-3 px-4">Type</th>
                                    <th className="py-3 px-4">Difficulty</th>
                                    <th className="py-3 px-4">Status</th>
                                    <th className="py-3 px-4">Version</th>
                                    <th className="py-3 px-4">Last Updated</th>
                                    <th className="py-3 px-6 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border text-sm">
                                {data.results.map((q) => {
                                    const activeVersion = q.latest_version;
                                    const formattedDate = new Date(q.updated_at).toLocaleDateString(
                                        undefined,
                                        {
                                            month: "short",
                                            day: "numeric",
                                            year: "numeric",
                                        },
                                    );

                                    return (
                                        <tr
                                            key={q.id}
                                            onClick={() =>
                                                navigate(`/admin/question-bank/questions/${q.id}`)
                                            }
                                            className="hover:bg-surface-muted/50 cursor-pointer transition-colors"
                                        >
                                            <td className="py-4 px-6 max-w-md">
                                                <div className="font-medium text-foreground line-clamp-2">
                                                    {activeVersion?.text || "Untitled Question"}
                                                </div>
                                                <div className="text-[11px] text-foreground-muted font-mono mt-0.5">
                                                    ID: {q.id.slice(0, 8)}...
                                                </div>
                                            </td>

                                            <td className="py-4 px-4 whitespace-nowrap">
                                                <span className="text-xs font-semibold text-neutral-700">
                                                    {activeVersion?.question_type || "—"}
                                                </span>
                                            </td>

                                            <td className="py-4 px-4 whitespace-nowrap">
                                                <Badge
                                                    variant={
                                                        activeVersion?.difficulty === "HARD"
                                                            ? "danger"
                                                            : activeVersion?.difficulty === "MEDIUM"
                                                            ? "warning"
                                                            : "success"
                                                    }
                                                    size="sm"
                                                >
                                                    {activeVersion?.difficulty || "—"}
                                                </Badge>
                                            </td>

                                            <td className="py-4 px-4 whitespace-nowrap">
                                                {activeVersion ? (
                                                    <QuestionStatusBadge
                                                        status={activeVersion.status}
                                                        size="sm"
                                                    />
                                                ) : (
                                                    "—"
                                                )}
                                            </td>

                                            <td className="py-4 px-4 whitespace-nowrap">
                                                <span className="font-mono text-xs font-bold text-neutral-700">
                                                    v{activeVersion?.version_number || 1}
                                                </span>
                                                <span className="text-[11px] text-neutral-400 block">
                                                    {q.version_count} total
                                                </span>
                                            </td>

                                            <td className="py-4 px-4 whitespace-nowrap text-xs text-foreground-muted">
                                                {formattedDate}
                                            </td>

                                            <td className="py-4 px-6 text-right whitespace-nowrap">
                                                <Link
                                                    to={`/admin/question-bank/questions/${q.id}`}
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="inline-flex text-xs font-semibold text-primary-600 hover:text-primary-800"
                                                >
                                                    Manage →
                                                </Link>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination footer */}
                {!isLoading && !isError && totalPages > 1 && (
                    <div className="p-4 border-t border-border flex items-center justify-between">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page <= 1}
                        >
                            Previous
                        </Button>
                        <span className="text-xs text-foreground-muted font-medium">
                            Page {page} of {totalPages}
                        </span>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                            disabled={page >= totalPages}
                        >
                            Next
                        </Button>
                    </div>
                )}
            </Card>
        </div>
    );
}
