import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";

export function ValueSection() {
    const pillars = [
        {
            tag: "Structural Rigor",
            title: "Strict 4-Level Curriculum Taxonomy",
            description:
                "Knowledge is categorized unambiguously into Domain → Subject → Chapter → Topic. No scattered questions or unstructured topic dumps.",
            icon: (
                <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
            ),
        },
        {
            tag: "Quality Control",
            title: "Versioned Question Bank",
            description:
                "Questions undergo explicit lifecycle state transitions (Draft → Review → Published). Every assessment pins exact QuestionVersion IDs for complete reproducibility.",
            icon: (
                <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            ),
        },
        {
            tag: "Standardized Testing",
            title: "Dual Evaluation Assessment Engine",
            description:
                "Enforces strict timers, negative-marking penalization formulas, and structured rubrics for both objective MCQs and descriptive analytical answers.",
            icon: (
                <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
            ),
        },
        {
            tag: "Auditability",
            title: "Deterministic Attempt Auditing",
            description:
                "Every answer selection, revision, and submission is recorded immutably. Scores are computed against pinned answer keys with complete transparency.",
            icon: (
                <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
            ),
        },
    ];

    return (
        <section id="curriculum" className="py-20 bg-surface border-b border-border">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
                    <Badge variant="primary" size="md">
                        Why Nexora
                    </Badge>
                    <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900">
                        Engineered for serious mastery.
                    </h2>
                    <p className="text-base sm:text-lg text-foreground-muted leading-relaxed">
                        Commercial learning platforms often prioritize gamified metrics over academic depth. Nexora focuses on structural clarity, deterministic rigor, and transparent evaluations.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {pillars.map((pillar) => (
                        <Card key={pillar.title} className="p-2 border-border/80 hover:border-neutral-300 transition-all">
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="w-10 h-10 rounded-lg bg-primary-50 border border-primary-100 flex items-center justify-center">
                                        {pillar.icon}
                                    </div>
                                    <Badge variant="default" size="sm">
                                        {pillar.tag}
                                    </Badge>
                                </div>
                                <CardTitle className="text-lg font-bold text-neutral-900">
                                    {pillar.title}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription className="text-sm text-foreground-muted leading-relaxed">
                                    {pillar.description}
                                </CardDescription>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
}
