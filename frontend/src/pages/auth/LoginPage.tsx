import { BrandLogo } from "@/shared/ui/BrandLogo";
import { LoginForm } from "@/features/auth";

export function LoginPage() {
    return (
        <div className="w-full max-w-4xl mx-auto shadow-md rounded-2xl overflow-hidden border border-border bg-surface grid grid-cols-1 lg:grid-cols-12">
            {/* Left Column: Nexora Branding & Academic Philosophy (Desktop) */}
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
                            Nexora Platform
                        </span>
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-xl font-bold tracking-tight text-white">
                            Rigorous preparation. Uncompromising clarity.
                        </h2>
                        <p className="text-xs text-neutral-300 leading-relaxed font-normal">
                            Systematic curriculum taxonomy, deterministic scoring, and detailed question audits engineered for serious aspirants.
                        </p>
                    </div>
                </div>

                <div className="relative z-10 space-y-3 pt-6 border-t border-neutral-800">
                    <blockquote className="text-xs italic text-neutral-400 leading-relaxed">
                        &ldquo;Discipline in conceptual preparation yields confidence in competitive examination.&rdquo;
                    </blockquote>
                    <div className="flex items-center gap-2 text-[11px] text-neutral-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        <span>Structured Learning · Practice · Assessment</span>
                    </div>
                </div>
            </div>

            {/* Right Column: Authentication Form */}
            <div className="lg:col-span-7 p-6 sm:p-8 lg:p-10 flex flex-col justify-center">
                <div className="space-y-2 mb-6 text-center sm:text-left">
                    <div className="lg:hidden flex justify-center mb-3">
                        <BrandLogo size="md" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground">
                        Sign in to Nexora
                    </h1>
                    <p className="text-sm text-foreground-muted">
                        Enter your credentials to access your platform account
                    </p>
                </div>

                <LoginForm />
            </div>
        </div>
    );
}
