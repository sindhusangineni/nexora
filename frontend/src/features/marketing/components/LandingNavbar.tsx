import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

import { BrandLogo } from "@/shared/ui/BrandLogo";
import { Button } from "@/shared/ui/Button";
import { useAuth } from "@/features/auth";

export function LandingNavbar() {
    const { isAuthenticated, isSuperadmin } = useAuth();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        if (!mobileMenuOpen) return;
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                setMobileMenuOpen(false);
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [mobileMenuOpen]);

    const dashboardPath = isSuperadmin ? "/admin/dashboard" : "/student/dashboard";

    const navLinks = [
        { label: "Curriculum", href: "#curriculum" },
        { label: "Assessments", href: "#assessments" },
        { label: "Methodology", href: "#methodology" },
        { label: "How It Works", href: "#how-it-works" },
    ];

    return (
        <header className="sticky top-0 z-40 w-full border-b border-border bg-surface/90 backdrop-blur-md transition-all">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                {/* Brand */}
                <BrandLogo to="/" size="md" />

                {/* Desktop Navigation Links */}
                <nav className="hidden md:flex items-center space-x-8" aria-label="Main Navigation">
                    {navLinks.map((link) => (
                        <a
                            key={link.label}
                            href={link.href}
                            className="text-sm font-medium text-foreground-muted hover:text-foreground transition-colors"
                        >
                            {link.label}
                        </a>
                    ))}
                </nav>

                {/* Desktop Auth CTAs */}
                <div className="hidden md:flex items-center space-x-3">
                    {isAuthenticated ? (
                        <Link to={dashboardPath}>
                            <Button variant="primary" size="sm">
                                Go to Dashboard
                            </Button>
                        </Link>
                    ) : (
                        <>
                            <Link to="/login">
                                <Button variant="ghost" size="sm">
                                    Sign in
                                </Button>
                            </Link>
                            <Link to="/signup">
                                <Button variant="primary" size="sm">
                                    Get started
                                </Button>
                            </Link>
                        </>
                    )}
                </div>

                {/* Mobile Menu Button */}
                <div className="flex md:hidden items-center">
                    <button
                        type="button"
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        aria-expanded={mobileMenuOpen}
                        aria-controls="mobile-nav-menu"
                        aria-label="Toggle navigation menu"
                        className="min-w-[44px] min-h-[44px] p-2 flex items-center justify-center rounded-lg text-foreground-muted hover:text-foreground hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-primary-500 cursor-pointer"
                    >
                        <svg
                            className="w-6 h-6"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth="1.75"
                        >
                            {mobileMenuOpen ? (
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            ) : (
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                                />
                            )}
                        </svg>
                    </button>
                </div>
            </div>

            {/* Mobile Menu Dropdown */}
            {mobileMenuOpen && (
                <div
                    id="mobile-nav-menu"
                    className="md:hidden border-b border-border bg-surface px-4 pt-2 pb-6 space-y-3"
                >
                    <nav className="flex flex-col space-y-2" aria-label="Mobile Navigation">
                        {navLinks.map((link) => (
                            <a
                                key={link.label}
                                href={link.href}
                                onClick={() => setMobileMenuOpen(false)}
                                className="px-3 py-2 text-base font-medium rounded-md text-foreground-muted hover:text-foreground hover:bg-neutral-100"
                            >
                                {link.label}
                            </a>
                        ))}
                    </nav>

                    <div className="pt-3 border-t border-border flex flex-col space-y-2">
                        {isAuthenticated ? (
                            <Link to={dashboardPath} onClick={() => setMobileMenuOpen(false)}>
                                <Button variant="primary" size="md" className="w-full">
                                    Go to Dashboard
                                </Button>
                            </Link>
                        ) : (
                            <>
                                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                                    <Button variant="secondary" size="md" className="w-full">
                                        Sign in
                                    </Button>
                                </Link>
                                <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                                    <Button variant="primary" size="md" className="w-full">
                                        Get started
                                    </Button>
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            )}
        </header>
    );
}
