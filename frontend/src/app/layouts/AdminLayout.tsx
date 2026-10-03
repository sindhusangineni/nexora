import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { useAuth } from "@/features/auth";

export function AdminLayout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate("/login", { replace: true });
    };

    const navItems = [
        { to: "/admin/dashboard", label: "Dashboard" },
        { to: "/admin/learning", label: "Learning" },
        { to: "/admin/question-bank", label: "Question Bank" },
        { to: "/admin/assessments", label: "Assessments" },
        { to: "/admin/attempts", label: "Attempts" },
    ];

    return (
        <div className="flex flex-col min-h-screen bg-background">
            {/* Header */}
            <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-border bg-surface shadow-xs">
                <div className="flex items-center space-x-3">
                    <span className="text-xl font-bold tracking-tight text-neutral-900">
                        Nexora
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-neutral-100 text-neutral-800 border border-neutral-300">
                        Superadmin Administration
                    </span>
                </div>

                <div className="flex items-center space-x-4">
                    <span className="text-sm font-medium text-foreground-muted hidden sm:inline-block">
                        {user?.email}
                    </span>
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleLogout}
                        aria-label="Log out of admin portal"
                    >
                        Sign out
                    </Button>
                </div>
            </header>

            <div className="flex-1 flex flex-col md:flex-row">
                {/* Sidebar */}
                <aside className="w-full md:w-64 bg-surface border-b md:border-b-0 md:border-r border-border p-4">
                    <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wider px-3 mb-2">
                        Administration
                    </div>
                    <nav className="space-y-1" aria-label="Admin Navigation">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.to}
                                to={item.to}
                                className={({ isActive }) =>
                                    `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                                        isActive
                                            ? "bg-neutral-100 text-neutral-900 font-semibold"
                                            : "text-foreground-muted hover:bg-neutral-100 hover:text-foreground"
                                    }`
                                }
                            >
                                {item.label}
                            </NavLink>
                        ))}
                    </nav>
                </aside>

                {/* Main Content */}
                <main className="flex-1 p-6 md:p-8 overflow-y-auto">
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
