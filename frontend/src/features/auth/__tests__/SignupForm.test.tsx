import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";

import { SignupForm } from "../components/SignupForm";
import { authApi } from "../api/authApi";
import { ApiError } from "@/lib/api";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    };
});

describe("SignupForm Component", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("renders all inputs and disabled submit button initially", () => {
        render(
            <BrowserRouter>
                <SignupForm />
            </BrowserRouter>,
        );

        expect(screen.getByLabelText(/^email address/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/^confirm password/i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /create account/i })).toBeDisabled();
    });

    it("enables submit button only when all fields are populated", async () => {
        const user = userEvent.setup();
        render(
            <BrowserRouter>
                <SignupForm />
            </BrowserRouter>,
        );

        const emailInput = screen.getByLabelText(/^email address/i);
        const passInput = screen.getByLabelText(/^password/i);
        const confirmInput = screen.getByLabelText(/^confirm password/i);
        const submitBtn = screen.getByRole("button", { name: /create account/i });

        await user.type(emailInput, "newuser@example.com");
        expect(submitBtn).toBeDisabled();

        await user.type(passInput, "Password123!");
        expect(submitBtn).toBeDisabled();

        await user.type(confirmInput, "Password123!");
        expect(submitBtn).toBeEnabled();
    });

    it("shows client-side validation error when password is shorter than 8 characters", async () => {
        const user = userEvent.setup();
        render(
            <BrowserRouter>
                <SignupForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/^email address/i), "newuser@example.com");
        await user.type(screen.getByLabelText(/^password/i), "short");
        await user.type(screen.getByLabelText(/^confirm password/i), "short");
        await user.click(screen.getByRole("button", { name: /create account/i }));

        expect(screen.getByText(/password must be at least 8 characters long/i)).toBeInTheDocument();
    });

    it("shows client-side validation error when passwords do not match", async () => {
        const user = userEvent.setup();
        render(
            <BrowserRouter>
                <SignupForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/^email address/i), "newuser@example.com");
        await user.type(screen.getByLabelText(/^password/i), "Password123!");
        await user.type(screen.getByLabelText(/^confirm password/i), "PasswordMismatch!");
        await user.click(screen.getByRole("button", { name: /create account/i }));

        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });

    it("successfully registers and displays success confirmation screen", async () => {
        const user = userEvent.setup();
        const registerSpy = vi.spyOn(authApi, "register").mockResolvedValueOnce({
            message: "User registered successfully.",
            user: {
                id: "new-user-1",
                email: "newstudent@example.com",
                email_verified: false,
                roles: ["student"],
            },
        });

        render(
            <BrowserRouter>
                <SignupForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/^email address/i), "newstudent@example.com");
        await user.type(screen.getByLabelText(/^password/i), "StrongPassword123!");
        await user.type(screen.getByLabelText(/^confirm password/i), "StrongPassword123!");
        await user.click(screen.getByRole("button", { name: /create account/i }));

        expect(registerSpy).toHaveBeenCalledWith({
            email: "newstudent@example.com",
            password: "StrongPassword123!",
            password_confirmation: "StrongPassword123!",
        });

        expect(screen.getByText(/account created successfully/i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /proceed to sign in/i })).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: /proceed to sign in/i }));
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });

    it("displays error message when registration fails with ApiError", async () => {
        const user = userEvent.setup();
        vi.spyOn(authApi, "register").mockRejectedValueOnce(
            new ApiError({
                code: "REGISTRATION_FAILED",
                message: "A user with this email already exists.",
                status: 400,
            }),
        );

        render(
            <BrowserRouter>
                <SignupForm />
            </BrowserRouter>,
        );

        await user.type(screen.getByLabelText(/^email address/i), "existing@example.com");
        await user.type(screen.getByLabelText(/^password/i), "StrongPassword123!");
        await user.type(screen.getByLabelText(/^confirm password/i), "StrongPassword123!");
        await user.click(screen.getByRole("button", { name: /create account/i }));

        expect(screen.getByRole("alert")).toHaveTextContent("A user with this email already exists.");
    });
});
