import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { OfflineBanner } from "../OfflineBanner";
import { PwaInstallBanner } from "../PwaInstallBanner";
import { useNetworkStatus } from "../useNetworkStatus";

function NetworkStatusProbe() {
    const { isOnline } = useNetworkStatus();
    return <span data-testid="network-status">{isOnline ? "online" : "offline"}</span>;
}

describe("PWA and Network Status components", () => {
    describe("useNetworkStatus", () => {
        it("returns true when navigator is online", () => {
            render(<NetworkStatusProbe />);
            expect(screen.getByTestId("network-status")).toHaveTextContent("online");
        });

        it("updates when offline and online events fire", () => {
            render(<NetworkStatusProbe />);
            expect(screen.getByTestId("network-status")).toHaveTextContent("online");

            act(() => {
                window.dispatchEvent(new Event("offline"));
            });
            expect(screen.getByTestId("network-status")).toHaveTextContent("offline");

            act(() => {
                window.dispatchEvent(new Event("online"));
            });
            expect(screen.getByTestId("network-status")).toHaveTextContent("online");
        });
    });

    describe("OfflineBanner", () => {
        it("does not render when online", () => {
            const { container } = render(<OfflineBanner />);
            expect(container.firstChild).toBeNull();
        });

        it("renders warning banner when offline", () => {
            render(<OfflineBanner />);
            act(() => {
                window.dispatchEvent(new Event("offline"));
            });

            expect(screen.getByRole("status")).toBeInTheDocument();
            expect(
                screen.getByText(/You appear to be offline/i),
            ).toBeInTheDocument();
            expect(
                screen.getByText(/Protected assessment operations require an active network connection/i),
            ).toBeInTheDocument();
        });
    });

    describe("PwaInstallBanner", () => {
        beforeEach(() => {
            sessionStorage.clear();
        });

        it("does not render if no beforeinstallprompt event occurred", () => {
            const { container } = render(<PwaInstallBanner />);
            expect(container.firstChild).toBeNull();
        });

        it("renders install prompt when beforeinstallprompt is dispatched", () => {
            render(<PwaInstallBanner />);

            const mockPrompt = vi.fn().mockResolvedValue(undefined);
            const event = new Event("beforeinstallprompt");
            Object.assign(event, {
                prompt: mockPrompt,
                userChoice: Promise.resolve({ outcome: "accepted" }),
            });

            act(() => {
                window.dispatchEvent(event);
            });

            expect(screen.getByText(/Install Nexora/i)).toBeInTheDocument();
            expect(screen.getByRole("button", { name: /Install App/i })).toBeInTheDocument();
        });

        it("dismisses prompt when Dismiss button is clicked", () => {
            render(<PwaInstallBanner />);

            const mockPrompt = vi.fn().mockResolvedValue(undefined);
            const event = new Event("beforeinstallprompt");
            Object.assign(event, {
                prompt: mockPrompt,
                userChoice: Promise.resolve({ outcome: "dismissed" }),
            });

            act(() => {
                window.dispatchEvent(event);
            });

            const dismissButton = screen.getByRole("button", { name: /Dismiss install prompt/i });
            fireEvent.click(dismissButton);

            expect(screen.queryByText(/Install Nexora/i)).not.toBeInTheDocument();
            expect(sessionStorage.getItem("nexora_pwa_dismissed")).toBe("true");
        });
    });
});
