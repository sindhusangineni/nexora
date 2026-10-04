import { Link } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/shared/ui/Card";

export function HeroSection() {
    return (
        <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28 border-b border-border bg-gradient-to-b from-surface to-background">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
                    {/* Left: Product Messaging */}
                    <div className="lg:col-span-6 space-y-6 text-center lg:text-left">
                        <div className="inline-flex items-center gap-2">
                            <Badge variant="primary" size="md">
                                Next-Gen Academic Preparation
                            </Badge>
                            <span className="text-xs font-medium text-foreground-muted hidden sm:inline-block">
                                UPSC & Comprehensive Assessments
                            </span>
                        </div>

                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-neutral-900 leading-[1.12]">
                            Master your preparation. <br className="hidden sm:inline" />
                            <span className="text-primary-600">One concept at a time.</span>
                        </h1>

                        <p className="text-lg sm:text-xl text-foreground-muted max-w-2xl mx-auto lg:mx-0 leading-relaxed font-normal">
                            Structured learning, objective question drills, and rigorous timed assessments designed for serious learners. Clear hierarchy from domains down to individual concepts.
                        </p>

                        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
                            <Link to="/signup" className="w-full sm:w-auto">
                                <Button
                                    variant="primary"
                                    size="lg"
                                    className="w-full sm:w-auto text-base px-8 py-3 shadow-sm hover:shadow"
                                >
                                    Start learning
                                </Button>
                            </Link>
                            <Link to="/login" className="w-full sm:w-auto">
                                <Button
                                    variant="secondary"
                                    size="lg"
                                    className="w-full sm:w-auto text-base px-6 py-3"
                                >
                                    Sign in
                                </Button>
                            </Link>
                        </div>

                        <div className="pt-4 flex items-center justify-center lg:justify-start gap-8 text-xs text-foreground-muted border-t border-border/80">
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                <span>Domain-driven taxonomy</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary-500"></span>
                                <span>Deterministic evaluation</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                                <span>Immutable attempt audits</span>
                            </div>
                        </div>
                    </div>

                    {/* Right: Realistic Product UI Preview */}
                    <div className="lg:col-span-6 relative">
                        {/* Background subtle glow */}
                        <div
                            className="absolute -inset-1.5 bg-gradient-to-r from-primary-500/10 via-primary-600/10 to-indigo-500/10 rounded-2xl blur-xl opacity-70"
                            aria-hidden="true"
                        />

                        {/* Interactive UI Mockup Stack */}
                        <div className="relative space-y-4">
                            {/* Card 1: Curriculum Hierarchy in Action */}
                            <Card className="shadow-md border-border/90">
                                <CardHeader className="pb-3 border-b border-border/60 bg-surface-muted/30">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="w-2.5 h-2.5 rounded-full bg-primary-600"></span>
                                            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                                                Curriculum Hierarchy
                                            </span>
                                        </div>
                                        <Badge variant="outline" size="sm">
                                            Domain / GS-II
                                        </Badge>
                                    </div>
                                    <CardTitle as="h2" className="text-base font-bold text-neutral-900 mt-1">
                                        Indian Polity & Governance
                                    </CardTitle>
                                    <CardDescription>
                                        Chapter 3: Constitutional Framework & Fundamental Rights
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="pt-4 space-y-2.5">
                                    {/* Topic rows */}
                                    <div className="flex items-center justify-between p-2.5 rounded-lg bg-primary-50/50 border border-primary-100/80">
                                        <div className="flex items-center gap-2.5">
                                            <div className="w-6 h-6 rounded bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
                                                1
                                            </div>
                                            <div>
                                                <div className="text-sm font-semibold text-neutral-900">
                                                    Preamble & Basic Structure Doctrine
                                                </div>
                                                <div className="text-xs text-neutral-500">
                                                    Kesavananda Bharati principles & amendments
                                                </div>
                                            </div>
                                        </div>
                                        <Badge variant="success" size="sm">
                                            Mastered
                                        </Badge>
                                    </div>

                                    <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border">
                                        <div className="flex items-center gap-2.5">
                                            <div className="w-6 h-6 rounded bg-neutral-100 text-neutral-700 flex items-center justify-center text-xs font-bold">
                                                2
                                            </div>
                                            <div>
                                                <div className="text-sm font-semibold text-neutral-900">
                                                    Article 21: Protection of Life & Personal Liberty
                                                </div>
                                                <div className="text-xs text-neutral-500">
                                                    Maneka Gandhi judgment & due process
                                                </div>
                                            </div>
                                        </div>
                                        <Badge variant="primary" size="sm">
                                            In Review
                                        </Badge>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Card 2: Realistic Assessment Question Card */}
                            <Card className="shadow-lg border-primary-200/60 bg-surface">
                                <div className="p-4 bg-primary-950 text-white rounded-t-xl flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-primary-800 text-primary-200">
                                            Mock Assessment #4
                                        </span>
                                        <span className="text-xs text-neutral-300 font-mono">
                                            Q 14 / 100
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 font-mono text-xs text-neutral-300">
                                        <svg
                                            className="w-4 h-4 text-amber-400"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth="2"
                                                d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                                            />
                                        </svg>
                                        <span>01:42:10</span>
                                    </div>
                                </div>
                                <div className="p-5 space-y-3">
                                    <p className="text-sm font-medium text-neutral-900 leading-snug">
                                        Consider the following statements regarding the writ jurisdiction of the Supreme Court and High Courts under the Constitution of India:
                                    </p>
                                    <div className="space-y-2 text-xs">
                                        <div className="p-2 rounded border border-primary-200 bg-primary-50/60 text-primary-950 font-medium flex items-center justify-between">
                                            <span>A. The writ jurisdiction of the High Court under Article 226 is wider than that of the Supreme Court under Article 32.</span>
                                            <span className="w-4 h-4 rounded-full bg-primary-600 text-white flex items-center justify-center text-[10px]">✓</span>
                                        </div>
                                        <div className="p-2 rounded border border-border bg-surface text-neutral-700">
                                            <span>B. Article 32 can be invoked for ordinary legal rights beyond fundamental rights.</span>
                                        </div>
                                    </div>
                                    <div className="pt-2 flex items-center justify-between text-xs text-neutral-500 border-t border-border">
                                        <span>Marking: +2.0 / -0.66</span>
                                        <span className="font-semibold text-primary-600">Saved & Pinned</span>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
