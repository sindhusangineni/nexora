import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    CardFooter,
} from "@/shared/ui/Card";
import { EmptyState } from "@/shared/ui/EmptyState";

export function AdminDashboardPage() {
    const { user } = useAuth();

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Badge variant="default" size="sm">
                            Control Center
                        </Badge>
                        <span className="text-xs text-foreground-muted">Platform Administration</span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        Superadmin Administration
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Logged in as <span className="font-semibold text-foreground">{user?.email}</span>
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <Link to="/admin/learning">
                        <Button variant="primary" size="md">
                            Manage Curriculum
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Management Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-primary-50 border border-primary-100 flex items-center justify-center text-primary-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                                </svg>
                            </div>
                            <Badge variant="success" size="sm">
                                Active
                            </Badge>
                        </div>
                        <CardTitle className="text-base">Learning Taxonomy</CardTitle>
                        <CardDescription>
                            Configure and maintain domains, subjects, chapters, and topics.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-3 border-t border-border/60">
                        <Link to="/admin/learning" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                Manage Taxonomy
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>

                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <Badge variant="outline" size="sm">
                                Versioned
                            </Badge>
                        </div>
                        <CardTitle className="text-base">Question Bank</CardTitle>
                        <CardDescription>
                            Author, review, version, and publish objective and descriptive items.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-3 border-t border-border/60">
                        <Link to="/admin/question-bank" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                Question Bank
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>

                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                                </svg>
                            </div>
                            <Badge variant="outline" size="sm">
                                Engine
                            </Badge>
                        </div>
                        <CardTitle className="text-base">Assessments</CardTitle>
                        <CardDescription>
                            Configure blueprints, timer constraints, and generate pinned papers.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-3 border-t border-border/60">
                        <Link to="/admin/assessments" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                Assessments
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>

                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-neutral-100 border border-neutral-200 flex items-center justify-center text-neutral-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                            <Badge variant="default" size="sm">
                                Audit
                            </Badge>
                        </div>
                        <CardTitle className="text-base">Attempts & Grading</CardTitle>
                        <CardDescription>
                            Audit student attempts, evaluate descriptive answers, and manage cancellations.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-3 border-t border-border/60">
                        <Link to="/admin/attempts" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                Attempts & Grading
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>
            </div>

            {/* Platform Audit & Activity Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-8">
                    <Card>
                        <CardHeader>
                            <CardTitle>System Audit & Pending Evaluations</CardTitle>
                            <CardDescription>
                                Track attempt submissions requiring descriptive evaluation or audit review.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <EmptyState
                                title="No pending evaluations or audit alerts"
                                description="When students submit descriptive assessments requiring manual review, or when attempt timeouts require audit, records will populate here."
                                action={
                                    <Link to="/admin/learning">
                                        <Button variant="primary" size="sm">
                                            Open Taxonomy Manager
                                        </Button>
                                    </Link>
                                }
                            />
                        </CardContent>
                    </Card>
                </div>

                <div className="lg:col-span-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Architecture Directives</CardTitle>
                            <CardDescription>
                                Core domain invariants
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4 text-xs leading-relaxed text-foreground-muted">
                            <div className="p-3 rounded-lg bg-surface-muted border border-border space-y-1">
                                <span className="font-semibold text-neutral-900 block">Pinned Question Versions</span>
                                <p>Once an assessment paper is generated, question versions are immutably pinned to prevent mid-test edits.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-muted border border-border space-y-1">
                                <span className="font-semibold text-neutral-900 block">Deterministic Scoring</span>
                                <p>Objective evaluation calculates marks strictly against verified answer keys with penalty coefficients.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-muted border border-border space-y-1">
                                <span className="font-semibold text-neutral-900 block">Attempt Immutability</span>
                                <p>Submitted attempts cannot be modified. Cancellation requires explicit administrative audit justification.</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
