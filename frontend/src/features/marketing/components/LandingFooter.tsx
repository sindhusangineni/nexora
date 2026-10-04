import { Link } from "react-router-dom";

import { BrandLogo } from "@/shared/ui/BrandLogo";

export function LandingFooter() {
    return (
        <footer className="bg-surface border-t border-border py-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    {/* Brand info */}
                    <div className="md:col-span-2 space-y-3">
                        <BrandLogo to="/" size="md" />
                        <p className="text-sm text-foreground-muted max-w-sm leading-relaxed">
                            A serious, domain-oriented learning and assessment platform designed for structured mastery and deterministic evaluation.
                        </p>
                        <div className="flex items-center gap-2 text-xs text-neutral-500 pt-1">
                            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                            <span>Platform engine operational</span>
                        </div>
                    </div>

                    {/* Navigation */}
                    <div className="space-y-3">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-900">
                            Platform
                        </h4>
                        <ul className="space-y-2 text-sm text-foreground-muted">
                            <li>
                                <a href="#curriculum" className="hover:text-foreground transition-colors">
                                    Curriculum Taxonomy
                                </a>
                            </li>
                            <li>
                                <a href="#assessments" className="hover:text-foreground transition-colors">
                                    Assessments & Papers
                                </a>
                            </li>
                            <li>
                                <a href="#methodology" className="hover:text-foreground transition-colors">
                                    Methodology
                                </a>
                            </li>
                            <li>
                                <a href="#how-it-works" className="hover:text-foreground transition-colors">
                                    Preparation Lifecycle
                                </a>
                            </li>
                        </ul>
                    </div>

                    {/* Account */}
                    <div className="space-y-3">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-900">
                            Access
                        </h4>
                        <ul className="space-y-2 text-sm text-foreground-muted">
                            <li>
                                <Link to="/login" className="hover:text-foreground transition-colors">
                                    Sign In
                                </Link>
                            </li>
                            <li>
                                <Link to="/signup" className="hover:text-foreground transition-colors">
                                    Create Free Account
                                </Link>
                            </li>
                            <li>
                                <Link to="/student/dashboard" className="hover:text-foreground transition-colors">
                                    Student Portal
                                </Link>
                            </li>
                            <li>
                                <Link to="/admin/dashboard" className="hover:text-foreground transition-colors">
                                    Admin Console
                                </Link>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-foreground-muted">
                    <p>&copy; {new Date().getFullYear()} Nexora. All rights reserved.</p>
                    <p className="text-foreground-subtle">
                        Engineered for serious UPSC & academic preparation.
                    </p>
                </div>
            </div>
        </footer>
    );
}
