import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";

import { LoginForm } from "../components/LoginForm";
import * as useAuthModule from "../context/useAuth";
import { ApiError } from "@/lib/api";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
    return {
        ...actual,
        useNavigate: () => mockNavigate,
        useLocation: () => ({ state: null }),
    };
});

describe("LoginForm Component", () => {
    const mockLogin = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        vi.spyOn(useAuthModule, "useAuth").mockReturnValue({
            user: null,
            status: "unauthenticated",
            isAuthenticated: false,
            isStudent: false,
            isSuperadmin: false,
            login: mockLogin,
            logout: vi.fn(),
            checkAuth: vi.fn(),
        });
    });

    it("renders email and password inputs and disabled submit button initially", () => {
        render(
            <BrowserRouter>
                <LoginForm />
            </BrowserRouter>,
        );

        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /sign in/i })).toBeDisabled();
    });

    it("enables submit button only when both fields have values", async () => {
        const user = userEvent.setup();
        render(
            <BrowserRouter>
                <LoginForm />
            </BrowserRouter>,
        );

        const emailInput = screen.getByLabelText(/email address/i);
        const passwordInput = screen.getByLabelText(/password/i);
        const submitBtn = screen.getByRole("button", { name: /sign in/i });

        await user.type(emailInput, "test@example.com");
        expect(submitBtn).toBeDisabled();

        await user.type(passwordInput, "secret123");
        expect(submitBtn).toBeEnabled();
    });

    it("successfully logs in a student and navigates to student dashboard", async () => {
        const user = userEvent.setup();
        mockLogin.mockResolvedValueOnce({
            id: "student-1",
            email: "student@example.com",
            email_verified: true,
            roles: ["student"],
        });

        render(
            <BrowserRouter>
                <LoginForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/email address/i), "student@example.com");
        await user.type(screen.getByLabelText(/password/i), "Password123!");
        await user.click(screen.getByRole("button", { name: /sign in/i }));

        expect(mockLogin).toHaveBeenCalledWith({
            email: "student@example.com",
            password: "Password123!",
        });
        expect(mockNavigate).toHaveBeenCalledWith("/student/dashboard", { replace: true });
    });

    it("successfully logs in a superadmin and navigates to admin dashboard", async () => {
        const user = userEvent.setup();
        mockLogin.mockResolvedValueOnce({
            id: "admin-1",
            email: "admin@example.com",
            email_verified: true,
            roles: ["superadmin"],
        });

        render(
            <BrowserRouter>
                <LoginForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/email address/i), "admin@example.com");
        await user.type(screen.getByLabelText(/password/i), "Password123!");
        await user.click(screen.getByRole("button", { name: /sign in/i }));

        expect(mockNavigate).toHaveBeenCalledWith("/admin/dashboard", { replace: true });
    });

    it("displays error message when login fails with ApiError", async () => {
        const user = userEvent.setup();
        mockLogin.mockRejectedValueOnce(
            new ApiError({
                code: "INVALID_CREDENTIALS",
                message: "Invalid email or password.",
                status: 401,
            }),
        );

        render(
            <BrowserRouter>
                <LoginForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/email address/i), "bad@example.com");
        await user.type(screen.getByLabelText(/password/i), "wrongpass");
        await user.click(screen.getByRole("button", { name: /sign in/i }));

        expect(screen.getByRole("alert")).toHaveTextContent("Invalid email or password.");
    });
});
