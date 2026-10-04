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

export function StudentDashboardPage() {
    const { user } = useAuth();

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Badge variant="primary" size="sm">
                            Student Portal
                        </Badge>
                        <span className="text-xs text-foreground-muted">Academic Term 2026</span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        Student Dashboard
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Welcome back, <span className="font-semibold text-foreground">{user?.email}</span>
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <Link to="/student/learning">
                        <Button variant="primary" size="md">
                            Continue Learning
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Preparation Pillars / Navigation Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-primary-50 border border-primary-100 flex items-center justify-center text-primary-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                </svg>
                            </div>
                            <Badge variant="success" size="sm">
                                Available
                            </Badge>
                        </div>
                        <CardTitle className="text-lg">Curriculum & Taxonomy</CardTitle>
                        <CardDescription>
                            Browse structured domains, subjects, chapters, and topics. Review detailed syllabus concepts.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-4 border-t border-border/60">
                        <Link to="/student/learning" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                Explore Curriculum
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>

                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                                </svg>
                            </div>
                            <Badge variant="outline" size="sm">
                                Ready
                            </Badge>
                        </div>
                        <CardTitle className="text-lg">Assessments & Mocks</CardTitle>
                        <CardDescription>
                            Attempt timed objective and descriptive assessments generated with pinned question papers.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-4 border-t border-border/60">
                        <Link to="/student/assessments" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                View Assessments
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>

                <Card interactive className="flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                            <div className="w-10 h-10 rounded-lg bg-neutral-100 border border-neutral-200 flex items-center justify-center text-neutral-600">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <Badge variant="default" size="sm">
                                Audit Trail
                            </Badge>
                        </div>
                        <CardTitle className="text-lg">Attempt History & Scores</CardTitle>
                        <CardDescription>
                            Access complete submission audits, verified answer keys, and objective evaluation breakdowns.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="pt-4 border-t border-border/60">
                        <Link to="/student/attempts" className="w-full">
                            <Button variant="secondary" size="sm" className="w-full">
                                Review Attempts
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>
            </div>

            {/* Preparation Activity & Status (Clean Empty State) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-8">
                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Activity & Assessment Attempts</CardTitle>
                            <CardDescription>
                                Track your recent practice sessions and timed test submissions.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <EmptyState
                                title="No assessment attempts recorded yet"
                                description="When you undertake timed assessments or practice tests, your submission audits and deterministic evaluations will appear here."
                                action={
                                    <Link to="/student/learning">
                                        <Button variant="primary" size="sm">
                                            Start with Curriculum
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
                            <CardTitle>Study Guidance</CardTitle>
                            <CardDescription>
                                Academic preparation methodology
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4 text-xs leading-relaxed text-foreground-muted">
                            <div className="p-3 rounded-lg bg-surface-muted border border-border space-y-1">
                                <span className="font-semibold text-neutral-900 block">1. Systematic Coverage</span>
                                <p>Begin by exploring subjects and completing subtopics sequentially before attempting composite tests.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-muted border border-border space-y-1">
                                <span className="font-semibold text-neutral-900 block">2. Exam Simulation</span>
                                <p>Strict timers simulate actual exam conditions. Make careful use of the question review flags.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-muted border border-border space-y-1">
                                <span className="font-semibold text-neutral-900 block">3. Concept Remediation</span>
                                <p>Always review wrong answers against the verified answer key to reinforce weak areas.</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
