import { useAuth } from "@/features/auth";

export function AdminDashboardPage() {
    const { user } = useAuth();

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                    Superadmin Administration
                </h1>
                <p className="text-sm text-foreground-muted mt-1">
                    Logged in as <span className="font-semibold text-foreground">{user?.email}</span>
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">Learning Taxonomy</h2>
                    <p className="text-sm text-foreground-muted">
                        Manage domains, subjects, chapters, and topics.
                    </p>
                </div>

                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">Question Bank</h2>
                    <p className="text-sm text-foreground-muted">
                        Author, review, version, and publish assessment questions.
                    </p>
                </div>

                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">Assessments</h2>
                    <p className="text-sm text-foreground-muted">
                        Configure assessments, selection rules, and generate papers.
                    </p>
                </div>

                <div className="p-6 bg-surface rounded-lg border border-border shadow-xs space-y-2">
                    <h2 className="text-base font-semibold text-foreground">Attempts & Grading</h2>
                    <p className="text-sm text-foreground-muted">
                        Audit active attempts, evaluate descriptive answers, and manage cancellations.
                    </p>
                </div>
            </div>
        </div>
    );
}
