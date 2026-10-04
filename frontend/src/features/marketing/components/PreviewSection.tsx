import { Badge } from "@/shared/ui/Badge";
import { Card, CardContent } from "@/shared/ui/Card";

export function PreviewSection() {
    const workflowSteps = [
        {
            step: "01",
            title: "Structured Learning",
            description: "Explore domains, subjects, chapters, and topics through an intuitive hierarchy.",
            details: "Domain → Subject → Chapter → Topic",
        },
        {
            step: "02",
            title: "Focused Practice",
            description: "Target specific subtopics with curated, version-controlled questions.",
            details: "Multiple-choice & descriptive formats",
        },
        {
            step: "03",
            title: "Rigorous Assessment",
            description: "Sit for full-length timed mock tests with strict countdowns and question navigation.",
            details: "Pinned question versions & penalty rules",
        },
        {
            step: "04",
            title: "Objective Evaluation",
            description: "Instant deterministic grading for objective questions and structured rubrics for mains.",
            details: "Transparent answer key comparison",
        },
        {
            step: "05",
            title: "Concept Mastery",
            description: "Identify topic-level vulnerabilities and study directly where improvement is needed.",
            details: "Grounded, actionable feedback",
        },
    ];

    return (
        <section id="assessments" className="py-20 bg-background border-b border-border">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
                    <Badge variant="primary" size="md">
                        The Preparation Lifecycle
                    </Badge>
                    <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900">
                        From initial concept to exam readiness.
                    </h2>
                    <p className="text-base sm:text-lg text-foreground-muted leading-relaxed">
                        Nexora replaces unstructured cramming with a cohesive, reproducible learning loop designed to build enduring competence.
                    </p>
                </div>

                {/* Stepper container */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
                    {workflowSteps.map((item, index) => (
                        <div key={item.step} className="relative flex flex-col">
                            <Card className="h-full border-border/80 bg-surface hover:border-primary-200 transition-all">
                                <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs font-mono font-bold text-primary-600 px-2 py-0.5 rounded bg-primary-50">
                                                {item.step}
                                            </span>
                                            {index < 4 && (
                                                <span className="hidden md:inline-block text-neutral-300 text-sm">
                                                    →
                                                </span>
                                            )}
                                        </div>
                                        <h3 className="text-base font-bold text-neutral-900 pt-1">
                                            {item.title}
                                        </h3>
                                        <p className="text-xs text-foreground-muted leading-relaxed">
                                            {item.description}
                                        </p>
                                    </div>
                                    <div className="pt-3 border-t border-border/60">
                                        <span className="text-[11px] font-medium text-neutral-500 block">
                                            {item.details}
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    ))}
                </div>

                {/* Realistic Sample Scorecard & Answer Review Preview */}
                <div className="mt-14 max-w-4xl mx-auto">
                    <Card className="shadow-sm border-border bg-surface overflow-hidden">
                        <div className="bg-neutral-900 text-white px-6 py-4 flex flex-wrap items-center justify-between gap-4">
                            <div>
                                <span className="text-xs text-neutral-400 uppercase tracking-wider block">
                                    Attempt Result Preview (Illustrative)
                                </span>
                                <h4 className="text-base font-bold text-white">
                                    General Studies Paper I — Full Syllabus Mock #03
                                </h4>
                            </div>
                            <div className="flex items-center gap-3">
                                <Badge variant="success" size="md">
                                    Evaluated & Closed
                                </Badge>
                            </div>
                        </div>

                        <div className="p-6 grid grid-cols-2 sm:grid-cols-4 gap-4 border-b border-border bg-surface-muted/30 text-center">
                            <div className="p-3 bg-surface rounded-lg border border-border">
                                <span className="text-xs text-foreground-muted block">Total Questions</span>
                                <span className="text-lg font-bold text-neutral-900">100</span>
                            </div>
                            <div className="p-3 bg-surface rounded-lg border border-border">
                                <span className="text-xs text-foreground-muted block">Attempted</span>
                                <span className="text-lg font-bold text-primary-700">82</span>
                            </div>
                            <div className="p-3 bg-surface rounded-lg border border-border">
                                <span className="text-xs text-foreground-muted block">Accuracy</span>
                                <span className="text-lg font-bold text-emerald-700">76.8%</span>
                            </div>
                            <div className="p-3 bg-surface rounded-lg border border-border">
                                <span className="text-xs text-foreground-muted block">Calculated Score</span>
                                <span className="text-lg font-bold text-neutral-900 font-mono">118.68 / 200</span>
                            </div>
                        </div>

                        <div className="p-6 space-y-3">
                            <div className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                                Detailed Question Audit Example
                            </div>
                            <div className="p-4 rounded-lg bg-surface border border-border space-y-2">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="font-semibold text-neutral-900">Question 42 · Indian Economy</span>
                                    <span className="text-emerald-600 font-medium">Correct (+2.00 Marks)</span>
                                </div>
                                <p className="text-xs text-neutral-700">
                                    Which of the following constitutes the primary objective of the Monetary Policy Committee (MPC) in India?
                                </p>
                                <div className="text-xs text-neutral-500 bg-neutral-50 p-2.5 rounded border border-neutral-200">
                                    <strong className="text-neutral-700">Verified Answer:</strong> Price stability with a target of 4% (±2%) CPI inflation, while keeping in mind the objective of growth under Section 45ZB of the RBI Act.
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </section>
    );
}
