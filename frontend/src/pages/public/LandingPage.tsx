import {
    LandingNavbar,
    HeroSection,
    ValueSection,
    PreviewSection,
    HowItWorksSection,
    CtaSection,
    LandingFooter,
} from "@/features/marketing";

export function LandingPage() {
    return (
        <div className="min-h-screen flex flex-col bg-background text-foreground antialiased">
            <LandingNavbar />
            <main className="flex-1">
                <HeroSection />
                <ValueSection />
                <PreviewSection />
                <HowItWorksSection />
                <CtaSection />
            </main>
            <LandingFooter />
        </div>
    );
}
