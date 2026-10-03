import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider } from "../context/AuthProvider";
import { useAuth } from "../context/useAuth";
import { authApi } from "../api/authApi";
import { getAccessToken } from "@/lib/api";

function TestConsumer() {
    const { user, status, isAuthenticated, isStudent, isSuperadmin, login, logout } = useAuth();
    return (
        <div>
            <div data-testid="status">{status}</div>
            <div data-testid="is-authenticated">{String(isAuthenticated)}</div>
            <div data-testid="is-student">{String(isStudent)}</div>
            <div data-testid="is-superadmin">{String(isSuperadmin)}</div>
            <div data-testid="user-email">{user?.email || "none"}</div>
            <button
                onClick={() =>
                    login({ email: "student@example.com", password: "Password123!" })
                }
            >
                Login Student
            </button>
            <button
                onClick={() =>
                    login({ email: "admin@example.com", password: "Password123!" })
                }
            >
                Login Admin
            </button>
            <button onClick={() => logout()}>Logout</button>
        </div>
    );
}

describe("AuthContext", () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        sessionStorage.clear();
        queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        });
        vi.restoreAllMocks();
    });

    it("starts in unauthenticated state when no session exists and refresh fails", async () => {
        vi.spyOn(authApi, "refreshToken").mockRejectedValueOnce(new Error("No cookie"));

        render(
            <QueryClientProvider client={queryClient}>
                <AuthProvider>
                    <TestConsumer />
                </AuthProvider>
            </QueryClientProvider>,
        );

        await waitFor(() => {
            expect(screen.getByTestId("status").textContent).toBe("unauthenticated");
        });
        expect(screen.getByTestId("is-authenticated").textContent).toBe("false");
        expect(screen.getByTestId("user-email").textContent).toBe("none");
    });

    it("updates state properly on successful student login", async () => {
        vi.spyOn(authApi, "refreshToken").mockRejectedValueOnce(new Error("No cookie"));
        vi.spyOn(authApi, "login").mockResolvedValueOnce({
            access: "student.access.jwt",
            user: {
                id: "student-1",
                email: "student@example.com",
                email_verified: true,
                roles: ["student"],
            },
        });

        render(
            <QueryClientProvider client={queryClient}>
                <AuthProvider>
                    <TestConsumer />
                </AuthProvider>
            </QueryClientProvider>,
        );

        await waitFor(() => {
            expect(screen.getByTestId("status").textContent).toBe("unauthenticated");
        });

        await act(async () => {
            screen.getByText("Login Student").click();
        });

        expect(screen.getByTestId("status").textContent).toBe("authenticated");
        expect(screen.getByTestId("is-authenticated").textContent).toBe("true");
        expect(screen.getByTestId("is-student").textContent).toBe("true");
        expect(screen.getByTestId("is-superadmin").textContent).toBe("false");
        expect(screen.getByTestId("user-email").textContent).toBe("student@example.com");
        expect(getAccessToken()).toBe("student.access.jwt");
    });

    it("updates state properly on successful superadmin login", async () => {
        vi.spyOn(authApi, "refreshToken").mockRejectedValueOnce(new Error("No cookie"));
        vi.spyOn(authApi, "login").mockResolvedValueOnce({
            access: "admin.access.jwt",
            user: {
                id: "admin-1",
                email: "admin@example.com",
                email_verified: true,
                roles: ["superadmin"],
            },
        });

        render(
            <QueryClientProvider client={queryClient}>
                <AuthProvider>
                    <TestConsumer />
                </AuthProvider>
            </QueryClientProvider>,
        );

        await waitFor(() => {
            expect(screen.getByTestId("status").textContent).toBe("unauthenticated");
        });

        await act(async () => {
            screen.getByText("Login Admin").click();
        });

        expect(screen.getByTestId("status").textContent).toBe("authenticated");
        expect(screen.getByTestId("is-authenticated").textContent).toBe("true");
        expect(screen.getByTestId("is-student").textContent).toBe("false");
        expect(screen.getByTestId("is-superadmin").textContent).toBe("true");
        expect(screen.getByTestId("user-email").textContent).toBe("admin@example.com");
        expect(getAccessToken()).toBe("admin.access.jwt");
    });

    it("clears user, token, and resets state upon logout", async () => {
        vi.spyOn(authApi, "refreshToken").mockRejectedValueOnce(new Error("No cookie"));
        vi.spyOn(authApi, "login").mockResolvedValueOnce({
            access: "test.jwt",
            user: { id: "1", email: "user@test.com", email_verified: true, roles: ["student"] },
        });
        vi.spyOn(authApi, "logout").mockResolvedValueOnce({ message: "Logged out" });

        render(
            <QueryClientProvider client={queryClient}>
                <AuthProvider>
                    <TestConsumer />
                </AuthProvider>
            </QueryClientProvider>,
        );

        await waitFor(() => {
            expect(screen.getByTestId("status").textContent).toBe("unauthenticated");
        });

        await act(async () => {
            screen.getByText("Login Student").click();
        });

        expect(screen.getByTestId("is-authenticated").textContent).toBe("true");

        await act(async () => {
            screen.getByText("Logout").click();
        });

        expect(screen.getByTestId("status").textContent).toBe("unauthenticated");
        expect(screen.getByTestId("is-authenticated").textContent).toBe("false");
        expect(screen.getByTestId("user-email").textContent).toBe("none");
        expect(getAccessToken()).toBeNull();
    });
});
