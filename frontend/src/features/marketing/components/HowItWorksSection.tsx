import { Badge } from "@/shared/ui/Badge";
import { Card, CardContent } from "@/shared/ui/Card";

export function HowItWorksSection() {
    const steps = [
        {
            number: "1",
            title: "Explore the Taxonomy",
            description:
                "Browse through domains like General Studies, Prelims Practice, and Optional Subjects. Delve into subjects, chapters, and topics with clear curriculum boundaries.",
            points: ["Domain to Topic hierarchy", "Systematic syllabus coverage", "No scattered materials"],
        },
        {
            number: "2",
            title: "Practice & Sit Assessments",
            description:
                "Take practice quizzes by topic or engage in timed full-length assessments. Questions are pinned to exact versions with official marking schemes and penalty deductions.",
            points: ["Realistic exam environment", "Configurable timers & negative marks", "Instant question navigation"],
        },
        {
            number: "3",
            title: "Audit & Elevate Mastery",
            description:
                "Analyze full audit trails of your submitted attempts. Review question explanations, evaluate descriptive response rubrics, and reinforce weak topic areas.",
            points: ["Deterministic evaluation", "Granular performance breakdowns", "Continuous targeted revision"],
        },
    ];

    return (
        <section id="how-it-works" className="py-20 bg-surface border-b border-border">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
                    <Badge variant="primary" size="md">
                        Methodology
                    </Badge>
                    <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900">
                        How Nexora works for you.
                    </h2>
                    <p className="text-base sm:text-lg text-foreground-muted leading-relaxed">
                        A transparent, disciplined path from first syllabus review to total exam confidence.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {steps.map((step) => (
                        <Card key={step.number} className="relative border-border/90 bg-background/50 hover:bg-surface transition-colors">
                            <CardContent className="p-8 space-y-4">
                                <div className="w-12 h-12 rounded-xl bg-primary-900 text-white font-bold text-lg flex items-center justify-center shadow-xs">
                                    {step.number}
                                </div>
                                <h3 className="text-xl font-bold text-neutral-900 pt-1">
                                    {step.title}
                                </h3>
                                <p className="text-sm text-foreground-muted leading-relaxed">
                                    {step.description}
                                </p>
                                <ul className="space-y-2 pt-2 border-t border-border/60">
                                    {step.points.map((point) => (
                                        <li key={point} className="flex items-center gap-2 text-xs text-neutral-600">
                                            <span className="w-1.5 h-1.5 rounded-full bg-primary-600"></span>
                                            <span>{point}</span>
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
}
