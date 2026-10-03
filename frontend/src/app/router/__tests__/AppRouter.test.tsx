import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AppRoutes } from "../AppRoutes";
import { AuthContext } from "@/features/auth/context/authContextDef";
import type { AuthContextValue, AuthUser } from "@/features/auth/types/auth.types";

function renderWithAuth(
    initialRoute: string,
    authOverrides: Partial<AuthContextValue> = {},
) {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });

    const defaultAuth: AuthContextValue = {
        user: null,
        status: "unauthenticated",
        isAuthenticated: false,
        isStudent: false,
        isSuperadmin: false,
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn(),
        ...authOverrides,
    };

    return render(
        <QueryClientProvider client={queryClient}>
            <AuthContext.Provider value={defaultAuth}>
                <MemoryRouter initialEntries={[initialRoute]}>
                    <AppRoutes />
                </MemoryRouter>
            </AuthContext.Provider>
        </QueryClientProvider>,
    );
}

describe("App Router & Route Protection", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("redirects unauthenticated user accessing /student/dashboard to /login", () => {
        renderWithAuth("/student/dashboard", {
            isAuthenticated: false,
            user: null,
            status: "unauthenticated",
        });

        expect(screen.getByRole("heading", { name: /sign in to nexora/i })).toBeInTheDocument();
    });

    it("redirects unauthenticated user accessing /admin/dashboard to /login", () => {
        renderWithAuth("/admin/dashboard", {
            isAuthenticated: false,
            user: null,
            status: "unauthenticated",
        });

        expect(screen.getByRole("heading", { name: /sign in to nexora/i })).toBeInTheDocument();
    });

    it("allows authenticated student to access /student/dashboard", () => {
        const studentUser: AuthUser = {
            id: "student-1",
            email: "student@example.com",
            email_verified: true,
            roles: ["student"],
        };

        renderWithAuth("/student/dashboard", {
            isAuthenticated: true,
            user: studentUser,
            status: "authenticated",
            isStudent: true,
            isSuperadmin: false,
        });

        expect(screen.getByRole("heading", { name: /student dashboard/i })).toBeInTheDocument();
        expect(screen.getAllByText("student@example.com").length).toBeGreaterThanOrEqual(1);
    });

    it("denies authenticated student access to /admin/dashboard and redirects to student home", () => {
        const studentUser: AuthUser = {
            id: "student-1",
            email: "student@example.com",
            email_verified: true,
            roles: ["student"],
        };

        renderWithAuth("/admin/dashboard", {
            isAuthenticated: true,
            user: studentUser,
            status: "authenticated",
            isStudent: true,
            isSuperadmin: false,
        });

        expect(screen.getByRole("heading", { name: /student dashboard/i })).toBeInTheDocument();
    });

    it("allows authenticated superadmin to access /admin/dashboard", () => {
        const adminUser: AuthUser = {
            id: "admin-1",
            email: "admin@example.com",
            email_verified: true,
            roles: ["superadmin"],
        };

        renderWithAuth("/admin/dashboard", {
            isAuthenticated: true,
            user: adminUser,
            status: "authenticated",
            isStudent: false,
            isSuperadmin: true,
        });

        expect(screen.getByRole("heading", { name: /superadmin administration/i })).toBeInTheDocument();
        expect(screen.getAllByText("admin@example.com").length).toBeGreaterThanOrEqual(1);
    });

    it("redirects authenticated student away from /login to student dashboard", () => {
        const studentUser: AuthUser = {
            id: "student-1",
            email: "student@example.com",
            email_verified: true,
            roles: ["student"],
        };

        renderWithAuth("/login", {
            isAuthenticated: true,
            user: studentUser,
            status: "authenticated",
            isStudent: true,
            isSuperadmin: false,
        });

        expect(screen.getByRole("heading", { name: /student dashboard/i })).toBeInTheDocument();
    });

    it("redirects authenticated superadmin away from /login to admin dashboard", () => {
        const adminUser: AuthUser = {
            id: "admin-1",
            email: "admin@example.com",
            email_verified: true,
            roles: ["superadmin"],
        };

        renderWithAuth("/login", {
            isAuthenticated: true,
            user: adminUser,
            status: "authenticated",
            isStudent: false,
            isSuperadmin: true,
        });

        expect(screen.getByRole("heading", { name: /superadmin administration/i })).toBeInTheDocument();
    });

    it("allows authenticated student to access /student/learning", async () => {
        const studentUser: AuthUser = {
            id: "student-1",
            email: "student@example.com",
            email_verified: true,
            roles: ["student"],
        };

        renderWithAuth("/student/learning", {
            isAuthenticated: true,
            user: studentUser,
            status: "authenticated",
            isStudent: true,
            isSuperadmin: false,
        });

        expect(
            screen.getByRole("heading", { name: /curriculum & learning/i }),
        ).toBeInTheDocument();
    });

    it("denies authenticated student access to /admin/learning and redirects to student home", () => {
        const studentUser: AuthUser = {
            id: "student-1",
            email: "student@example.com",
            email_verified: true,
            roles: ["student"],
        };

        renderWithAuth("/admin/learning", {
            isAuthenticated: true,
            user: studentUser,
            status: "authenticated",
            isStudent: true,
            isSuperadmin: false,
        });

        expect(
            screen.getByRole("heading", { name: /student dashboard/i }),
        ).toBeInTheDocument();
    });

    it("allows authenticated superadmin to access /admin/learning", async () => {
        const adminUser: AuthUser = {
            id: "admin-1",
            email: "admin@example.com",
            email_verified: true,
            roles: ["superadmin"],
        };

        renderWithAuth("/admin/learning", {
            isAuthenticated: true,
            user: adminUser,
            status: "authenticated",
            isStudent: false,
            isSuperadmin: true,
        });

        expect(
            screen.getByRole("heading", { name: /learning taxonomy management/i }),
        ).toBeInTheDocument();
    });

    it("renders 404 page for unknown routes", () => {
        renderWithAuth("/unknown-non-existent-route");

        expect(screen.getByRole("heading", { name: "404" })).toBeInTheDocument();
        expect(screen.getByText(/page not found/i)).toBeInTheDocument();
    });
});

