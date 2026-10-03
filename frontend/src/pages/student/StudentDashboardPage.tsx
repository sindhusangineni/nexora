import { useAuth } from "@/features/auth";

export function StudentDashboardPage() {
    const { user } = useAuth();

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                    Student Dashboard
                </h1>
                <p className="text-sm text-foreground-muted mt-1">
                    Welcome back, <span className="font-semibold text-foreground">{user?.email}</span>
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">Learning</h2>
                    <p className="text-sm text-foreground-muted">
                        Explore subjects, chapters, and curriculum topics.
                    </p>
                </div>

                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">Assessments</h2>
                    <p className="text-sm text-foreground-muted">
                        Browse active quizzes, mock assessments, and practice tests.
                    </p>
                </div>

                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">My Attempts</h2>
                    <p className="text-sm text-foreground-muted">
                        Review submitted attempts, scores, and performance feedback.
                    </p>
                </div>
            </div>
        </div>
    );
}
