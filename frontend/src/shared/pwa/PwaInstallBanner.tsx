import React from "react";
import { Button } from "@/shared/ui/Button";
import { usePwaInstall } from "./usePwaInstall";

export const PwaInstallBanner: React.FC = () => {
    const { canInstall, promptInstall, dismissInstall } = usePwaInstall();

    if (!canInstall) return null;

    return (
        <aside
            aria-label="Install Nexora App"
            className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:w-96 z-40 bg-surface border border-border-strong rounded-xl shadow-lg p-4 flex flex-col space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300"
        >
            <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                    <img
                        src="/pwa-192x192.png"
                        alt="Nexora Icon"
                        className="w-8 h-8 rounded-md shrink-0 shadow-xs"
                    />
                    <div>
                        <h4 className="text-xs font-bold text-foreground tracking-tight">
                            Install Nexora
                        </h4>
                        <p className="text-[11px] text-foreground-muted">
                            Fast, full-screen examination and learning workspace.
                        </p>
                    </div>
                </div>

                <button
                    type="button"
                    onClick={dismissInstall}
                    aria-label="Dismiss install prompt"
                    className="text-foreground-muted hover:text-foreground p-1 rounded-md text-xs hover:bg-neutral-100 min-w-[32px] min-h-[32px] flex items-center justify-center cursor-pointer"
                >
                    &times;
                </button>
            </div>

            <div className="flex items-center space-x-2 justify-end pt-1">
                <Button variant="ghost" size="sm" onClick={dismissInstall}>
                    Not now
                </Button>
                <Button variant="primary" size="sm" onClick={promptInstall}>
                    Install App
                </Button>
            </div>
        </aside>
    );
};
