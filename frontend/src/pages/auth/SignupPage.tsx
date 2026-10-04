import { BrandLogo } from "@/shared/ui/BrandLogo";
import { SignupForm } from "@/features/auth";

export function SignupPage() {
    return (
        <div className="w-full max-w-4xl mx-auto shadow-md rounded-2xl overflow-hidden border border-border bg-surface grid grid-cols-1 lg:grid-cols-12">
            {/* Left Column: Nexora Branding & Benefits (Desktop) */}
            <div className="hidden lg:flex lg:col-span-5 bg-neutral-900 text-white p-8 lg:p-10 flex-col justify-between relative overflow-hidden">
                {/* Background geometric accents */}
                <div
                    className="absolute inset-0 opacity-10 bg-[radial-gradient(#60a5fa_1px,transparent_1px)] [background-size:16px_16px]"
                    aria-hidden="true"
                />

                <div className="relative z-10 space-y-4">
                    <div className="inline-flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-primary-400"></span>
                        <span className="text-xs font-semibold uppercase tracking-wider text-neutral-300">
                            Join Nexora
                        </span>
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-xl font-bold tracking-tight text-white">
                            Begin your journey toward true mastery.
                        </h2>
                        <p className="text-xs text-neutral-300 leading-relaxed font-normal">
                            Access comprehensive taxonomy-driven curriculums, full-length timed assessments, and granular performance tracking.
                        </p>
                    </div>

                    <div className="pt-4 space-y-2.5 text-xs text-neutral-300">
                        <div className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full bg-primary-800 text-primary-300 flex items-center justify-center text-[10px] font-bold">✓</span>
                            <span>Direct access to student curriculum</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full bg-primary-800 text-primary-300 flex items-center justify-center text-[10px] font-bold">✓</span>
                            <span>Objective & descriptive practice papers</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full bg-primary-800 text-primary-300 flex items-center justify-center text-[10px] font-bold">✓</span>
                            <span>Instant, deterministic score evaluation</span>
                        </div>
                    </div>
                </div>

                <div className="relative z-10 pt-6 border-t border-neutral-800 text-[11px] text-neutral-400">
                    <span>Designed for UPSC, State PCS & high-stakes competitive examinations.</span>
                </div>
            </div>

            {/* Right Column: Registration Form */}
            <div className="lg:col-span-7 p-6 sm:p-8 lg:p-10 flex flex-col justify-center">
                <div className="space-y-2 mb-6 text-center sm:text-left">
                    <div className="lg:hidden flex justify-center mb-3">
                        <BrandLogo size="md" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground">
                        Create your Nexora account
                    </h1>
                    <p className="text-sm text-foreground-muted">
                        Enter your email and create a password to get started
                    </p>
                </div>

                <SignupForm />
            </div>
        </div>
    );
}
