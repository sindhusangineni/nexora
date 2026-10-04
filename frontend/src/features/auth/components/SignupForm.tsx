import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { parseApiError, type ApiError } from "@/lib/api";
import { authApi } from "../api/authApi";

export function SignupForm() {
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordConfirmation, setPasswordConfirmation] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [apiError, setApiError] = useState<ApiError | null>(null);
    const [clientErrors, setClientErrors] = useState<{
        passwordConfirmation?: string;
        password?: string;
    }>({});

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setApiError(null);
        setClientErrors({});

        const cleanEmail = email.trim();
        if (!cleanEmail || !password || !passwordConfirmation) {
            return;
        }

        if (password.length < 8) {
            setClientErrors({
                password: "Password must be at least 8 characters long.",
            });
            return;
        }

        if (password !== passwordConfirmation) {
            setClientErrors({
                passwordConfirmation: "Passwords do not match.",
            });
            return;
        }

        setIsLoading(true);
        try {
            await authApi.register({
                email: cleanEmail,
                password,
                password_confirmation: passwordConfirmation,
            });
            setIsSuccess(true);
        } catch (err) {
            setApiError(parseApiError(err));
        } finally {
            setIsLoading(false);
        }
    };

    if (isSuccess) {
        return (
            <div
                className="w-full max-w-md p-6 space-y-5 rounded-xl border border-emerald-200 bg-emerald-50/50 text-center"
                role="status"
                aria-live="polite"
            >
                <div className="w-12 h-12 mx-auto rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                    <svg
                        className="w-6 h-6"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth="2"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M4.5 12.75l6 6 9-13.5"
                        />
                    </svg>
                </div>
                <div className="space-y-1">
                    <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">
                        Account created successfully
                    </h2>
                    <p className="text-sm text-neutral-600">
                        Your account for <span className="font-medium text-neutral-900">{email}</span> is ready. You can now sign in to begin learning.
                    </p>
                </div>
                <div className="pt-2">
                    <Button
                        variant="primary"
                        size="lg"
                        className="w-full"
                        onClick={() => navigate("/login")}
                    >
                        Proceed to Sign in
                    </Button>
                </div>
            </div>
        );
    }

    const emailErrors = apiError?.fields?.email;
    const passwordErrors = apiError?.fields?.password || (clientErrors.password ? [clientErrors.password] : undefined);
    const confirmErrors = apiError?.fields?.password_confirmation || (clientErrors.passwordConfirmation ? [clientErrors.passwordConfirmation] : undefined);

    const isFormValid = email.trim() && password && passwordConfirmation;

    return (
        <form
            onSubmit={handleSubmit}
            className="w-full max-w-md space-y-5"
            noValidate
            aria-label="Registration form"
        >
            {apiError && !emailErrors && !passwordErrors && !confirmErrors && (
                <div
                    role="alert"
                    aria-live="polite"
                    className="p-3 text-sm rounded-lg bg-red-50 border border-red-200 text-danger"
                >
                    <p className="font-medium">{apiError.message}</p>
                </div>
            )}

            <div className="space-y-1.5">
                <label
                    htmlFor="signup-email"
                    className="block text-sm font-medium text-foreground tracking-tight"
                >
                    Email address
                </label>
                <input
                    id="signup-email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    aria-invalid={Boolean(emailErrors)}
                    aria-describedby={emailErrors ? "signup-email-error" : undefined}
                    placeholder="learner@example.com"
                    className={`w-full h-10 px-3.5 text-sm rounded-lg border bg-surface text-foreground transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 placeholder:text-foreground-subtle ${
                        emailErrors
                            ? "border-danger focus:ring-danger/25"
                            : "border-border hover:border-border-strong focus:ring-primary-500/20 focus:border-primary-600"
                    } disabled:opacity-50 disabled:bg-neutral-100`}
                />
                {emailErrors && (
                    <p id="signup-email-error" className="text-xs font-medium text-danger">
                        {emailErrors.join(" ")}
                    </p>
                )}
            </div>

            <div className="space-y-1.5">
                <label
                    htmlFor="signup-password"
                    className="block text-sm font-medium text-foreground tracking-tight"
                >
                    Password
                </label>
                <input
                    id="signup-password"
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    aria-invalid={Boolean(passwordErrors)}
                    aria-describedby={passwordErrors ? "signup-password-error" : undefined}
                    placeholder="At least 8 characters"
                    className={`w-full h-10 px-3.5 text-sm rounded-lg border bg-surface text-foreground transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 placeholder:text-foreground-subtle ${
                        passwordErrors
                            ? "border-danger focus:ring-danger/25"
                            : "border-border hover:border-border-strong focus:ring-primary-500/20 focus:border-primary-600"
                    } disabled:opacity-50 disabled:bg-neutral-100`}
                />
                {passwordErrors && (
                    <p id="signup-password-error" className="text-xs font-medium text-danger">
                        {passwordErrors.join(" ")}
                    </p>
                )}
            </div>

            <div className="space-y-1.5">
                <label
                    htmlFor="signup-password-confirm"
                    className="block text-sm font-medium text-foreground tracking-tight"
                >
                    Confirm password
                </label>
                <input
                    id="signup-password-confirm"
                    name="password_confirmation"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={passwordConfirmation}
                    onChange={(e) => setPasswordConfirmation(e.target.value)}
                    disabled={isLoading}
                    aria-invalid={Boolean(confirmErrors)}
                    aria-describedby={confirmErrors ? "signup-confirm-error" : undefined}
                    placeholder="Re-enter password"
                    className={`w-full h-10 px-3.5 text-sm rounded-lg border bg-surface text-foreground transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 placeholder:text-foreground-subtle ${
                        confirmErrors
                            ? "border-danger focus:ring-danger/25"
                            : "border-border hover:border-border-strong focus:ring-primary-500/20 focus:border-primary-600"
                    } disabled:opacity-50 disabled:bg-neutral-100`}
                />
                {confirmErrors && (
                    <p id="signup-confirm-error" className="text-xs font-medium text-danger">
                        {confirmErrors.join(" ")}
                    </p>
                )}
            </div>

            <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={isLoading}
                disabled={isLoading || !isFormValid}
                className="w-full shadow-xs"
            >
                {isLoading ? "Creating account..." : "Create account"}
            </Button>

            <div className="text-center pt-2">
                <p className="text-sm text-foreground-muted">
                    Already have an account?{" "}
                    <Link
                        to="/login"
                        className="font-semibold text-primary-600 hover:text-primary-700 underline-offset-4 hover:underline"
                    >
                        Sign in
                    </Link>
                </p>
            </div>
        </form>
    );
}
