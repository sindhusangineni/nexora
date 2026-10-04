import { useState, useEffect, useCallback } from "react";

interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

const DISMISS_KEY = "nexora_pwa_dismissed";

export function usePwaInstall() {
    const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
    const [isDismissed, setIsDismissed] = useState<boolean>(() => {
        try {
            return sessionStorage.getItem(DISMISS_KEY) === "true";
        } catch {
            return false;
        }
    });

    useEffect(() => {
        const handler = (e: Event) => {
            e.preventDefault();
            setDeferredPrompt(e as BeforeInstallPromptEvent);
        };

        window.addEventListener("beforeinstallprompt", handler);
        return () => window.removeEventListener("beforeinstallprompt", handler);
    }, []);

    const promptInstall = useCallback(async () => {
        if (!deferredPrompt) return;
        await deferredPrompt.prompt();
        const choice = await deferredPrompt.userChoice;
        if (choice.outcome === "accepted") {
            setDeferredPrompt(null);
        }
    }, [deferredPrompt]);

    const dismissInstall = useCallback(() => {
        setIsDismissed(true);
        try {
            sessionStorage.setItem(DISMISS_KEY, "true");
        } catch {
            // Ignore storage errors
        }
    }, []);

    const canInstall = Boolean(deferredPrompt && !isDismissed);

    return { canInstall, promptInstall, dismissInstall };
}
