import { useState, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { BrandLogo } from "@/shared/ui/BrandLogo";
import { useAuth } from "@/features/auth";

export function StudentLayout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Handle escape key
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

    const handleLogout = async () => {
        await logout();
        navigate("/login", { replace: true });
    };

    const navItems = [
        { to: "/student/dashboard", label: "Dashboard" },
        { to: "/student/learning", label: "Learning" },
        { to: "/student/assessments", label: "Assessments" },
        { to: "/student/attempts", label: "Attempts" },
    ];

    return (
        <div className="flex flex-col min-h-screen bg-background">
            {/* Header */}
            <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 border-b border-border bg-surface/95 backdrop-blur-xs shadow-2xs">
                <div className="flex items-center space-x-3">
                    {/* Mobile Menu Toggle Button */}
                    <button
                        type="button"
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        aria-expanded={mobileMenuOpen}
                        aria-controls="student-mobile-menu"
                        aria-label="Toggle student navigation menu"
                        className="md:hidden min-w-[44px] min-h-[44px] -ml-2 p-2 flex items-center justify-center rounded-lg text-foreground-muted hover:text-foreground hover:bg-neutral-100 transition-colors cursor-pointer"
                    >
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth="2"
                            aria-hidden="true"
                        >
                            {mobileMenuOpen ? (
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                            )}
                        </svg>
                    </button>

                    <BrandLogo to="/student/dashboard" size="sm" showWordmark={true} />
                    <span className="hidden xs:inline-block text-[11px] px-2 py-0.5 rounded-full font-medium bg-primary-50 text-primary-700 border border-primary-200">
                        Student
                    </span>
                </div>

                <div className="flex items-center space-x-3 sm:space-x-4">
                    <span className="text-xs sm:text-sm font-medium text-foreground-muted hidden sm:inline-block truncate max-w-[200px]">
                        {user?.email}
                    </span>
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleLogout}
                        aria-label="Log out of student portal"
                        className="min-h-[36px]"
                    >
                        Sign out
                    </Button>
                </div>
            </header>

            <div className="flex-1 flex flex-col md:flex-row">
                {/* Desktop Sidebar (hidden on mobile/tablet below md) */}
                <aside className="hidden md:block w-64 bg-surface border-r border-border p-4 shrink-0">
                    <nav className="space-y-1.5" aria-label="Student Navigation">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.to}
                                to={item.to}
                                className={({ isActive }) =>
                                    `flex items-center px-3.5 py-2.5 text-sm font-medium rounded-lg transition-colors min-h-[40px] ${
                                        isActive
                                            ? "bg-primary-50 text-primary-700 font-semibold"
                                            : "text-foreground-muted hover:bg-neutral-100 hover:text-foreground"
                                    }`
                                }
                            >
                                {item.label}
                            </NavLink>
                        ))}
                    </nav>
                </aside>

                {/* Mobile Drawer (visible only on small screens when open) */}
                {mobileMenuOpen && (
                    <div
                        id="student-mobile-menu"
                        className="md:hidden fixed inset-0 z-40 flex"
                        role="dialog"
                        aria-modal="true"
                        aria-label="Student Mobile Navigation"
                    >
                        {/* Backdrop */}
                        <div
                            className="fixed inset-0 bg-neutral-900/50 backdrop-blur-xs transition-opacity"
                            onClick={() => setMobileMenuOpen(false)}
                        />

                        {/* Slide-over panel */}
                        <div className="relative w-4/5 max-w-xs bg-surface h-full shadow-2xl p-5 flex flex-col z-50 animate-in slide-in-from-left duration-200">
                            <div className="flex items-center justify-between pb-4 border-b border-border">
                                <BrandLogo size="sm" showWordmark={true} />
                                <button
                                    type="button"
                                    onClick={() => setMobileMenuOpen(false)}
                                    aria-label="Close navigation"
                                    className="min-w-[44px] min-h-[44px] flex items-center justify-center -mr-2 text-foreground-muted hover:text-foreground rounded-lg hover:bg-neutral-100 cursor-pointer"
                                >
                                    <span aria-hidden="true" className="text-xl">&times;</span>
                                </button>
                            </div>

                            <div className="py-2 text-xs text-foreground-muted truncate">
                                Signed in as: <strong className="text-foreground">{user?.email}</strong>
                            </div>

                            <nav className="flex-1 py-4 space-y-1 overflow-y-auto" aria-label="Mobile Student Navigation">
                                {navItems.map((item) => (
                                    <NavLink
                                        key={item.to}
                                        to={item.to}
                                        onClick={() => setMobileMenuOpen(false)}
                                        className={({ isActive }) =>
                                            `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors min-h-[44px] ${
                                                isActive
                                                    ? "bg-primary-50 text-primary-700 font-semibold"
                                                    : "text-foreground-muted hover:bg-neutral-100 hover:text-foreground"
                                            }`
                                        }
                                    >
                                        {item.label}
                                    </NavLink>
                                ))}
                            </nav>

                            <div className="pt-4 border-t border-border">
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={handleLogout}
                                    className="w-full min-h-[44px]"
                                >
                                    Sign out
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Content */}
                <main className="flex-1 p-4 sm:p-6 md:p-8 overflow-y-auto w-full">
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
