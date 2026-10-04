import { Link } from "react-router-dom";

import { Button } from "@/shared/ui/Button";

export function CtaSection() {
    return (
        <section className="py-20 bg-neutral-900 text-white relative overflow-hidden">
            {/* Background subtle geometric accents */}
            <div
                className="absolute inset-0 opacity-10 bg-[radial-gradient(#60a5fa_1px,transparent_1px)] [background-size:16px_16px]"
                aria-hidden="true"
            />

            <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
                <span className="text-xs uppercase font-bold tracking-widest text-primary-400">
                    Serious Academic Preparation
                </span>

                <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
                    Begin structured preparation with Nexora today.
                </h2>

                <p className="text-base sm:text-lg text-neutral-300 max-w-2xl mx-auto leading-relaxed font-normal">
                    Experience structured domain taxonomies, reproducible assessments, and deterministic evaluations. Everything you need to prepare with clarity and confidence.
                </p>

                <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link to="/signup" className="w-full sm:w-auto">
                        <Button
                            variant="primary"
                            size="lg"
                            className="w-full sm:w-auto text-base px-8 py-3 bg-primary-600 hover:bg-primary-500 shadow-md"
                        >
                            Get started now
                        </Button>
                    </Link>
                    <Link to="/login" className="w-full sm:w-auto">
                        <Button
                            variant="secondary"
                            size="lg"
                            className="w-full sm:w-auto text-base px-8 py-3 border-neutral-700 bg-neutral-800 text-white hover:bg-neutral-700 hover:text-white"
                        >
                            Sign in to account
                        </Button>
                    </Link>
                </div>
            </div>
        </section>
    );
}
