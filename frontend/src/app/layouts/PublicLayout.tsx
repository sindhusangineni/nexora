import { Outlet } from "react-router-dom";

export function PublicLayout() {
    return (
        <div className="flex flex-col min-h-screen bg-background">
            <header className="border-b border-border bg-surface px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <span className="text-xl font-bold tracking-tight text-primary-600">
                            Nexora
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-neutral-100 text-neutral-600 border border-neutral-200">
                            Learning Platform
                        </span>
                    </div>
                </div>
            </header>

            <main className="flex-1 flex items-center justify-center p-6">
                <Outlet />
            </main>

            <footer className="border-t border-border bg-surface py-4 text-center text-xs text-foreground-muted">
                &copy; {new Date().getFullYear()} Nexora. All rights reserved.
            </footer>
        </div>
    );
}
