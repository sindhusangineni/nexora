import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";

import { LandingPage } from "@/pages/public/LandingPage";
import * as useAuthModule from "@/features/auth/context/useAuth";

describe("LandingPage Component", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.spyOn(useAuthModule, "useAuth").mockReturnValue({
            user: null,
            status: "unauthenticated",
            isAuthenticated: false,
            isStudent: false,
            isSuperadmin: false,
            login: vi.fn(),
            logout: vi.fn(),
            checkAuth: vi.fn(),
        });
    });

    it("renders the hero headline and core product value proposition", () => {
        render(
            <BrowserRouter>
                <LandingPage />
            </BrowserRouter>,
        );

        expect(
            screen.getByRole("heading", { name: /master your preparation/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/one concept at a time/i),
        ).toBeInTheDocument();
    });

    it("renders public navigation links and authentication CTAs for unauthenticated visitors", () => {
        render(
            <BrowserRouter>
                <LandingPage />
            </BrowserRouter>,
        );

        expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
        expect(screen.getAllByRole("button", { name: /sign in/i }).length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByRole("button", { name: /get started/i }).length).toBeGreaterThanOrEqual(1);
    });

    it("displays dashboard button when visitor is already authenticated", () => {
        vi.spyOn(useAuthModule, "useAuth").mockReturnValue({
            user: {
                id: "student-1",
                email: "student@example.com",
                email_verified: true,
                roles: ["student"],
            },
            status: "authenticated",
            isAuthenticated: true,
            isStudent: true,
            isSuperadmin: false,
            login: vi.fn(),
            logout: vi.fn(),
            checkAuth: vi.fn(),
        });

        render(
            <BrowserRouter>
                <LandingPage />
            </BrowserRouter>,
        );

        expect(screen.getByRole("button", { name: /go to dashboard/i })).toBeInTheDocument();
    });

    it("supports toggling the mobile navigation menu", async () => {
        const user = userEvent.setup();
        render(
            <BrowserRouter>
                <LandingPage />
            </BrowserRouter>,
        );

        const toggleBtn = screen.getByRole("button", { name: /toggle navigation menu/i });
        expect(toggleBtn).toBeInTheDocument();

        expect(screen.queryByRole("navigation", { name: /mobile navigation/i })).not.toBeInTheDocument();

        await user.click(toggleBtn);
        expect(screen.getByRole("navigation", { name: /mobile navigation/i })).toBeInTheDocument();

        await user.click(toggleBtn);
        expect(screen.queryByRole("navigation", { name: /mobile navigation/i })).not.toBeInTheDocument();
    });

    it("renders curriculum and assessment preview sections", () => {
        render(
            <BrowserRouter>
                <LandingPage />
            </BrowserRouter>,
        );

        expect(screen.getByRole("heading", { name: /engineered for serious mastery/i })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: /from initial concept to exam readiness/i })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: /how nexora works for you/i })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: /begin structured preparation with nexora today/i })).toBeInTheDocument();
    });
});
