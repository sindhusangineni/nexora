import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/Button";
import { parseApiError, type ApiError } from "@/lib/api";
import { useAuth } from "../context/useAuth";

export function LoginForm() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [apiError, setApiError] = useState<ApiError | null>(null);

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setApiError(null);

        const cleanEmail = email.trim();
        if (!cleanEmail || !password) {
            return;
        }

        setIsLoading(true);
        try {
            const user = await login({ email: cleanEmail, password });

            // Determine redirect destination
            const fromLocation = (location.state as { from?: { pathname: string } })?.from?.pathname;
            const isSuperadmin = user.roles.some((r) => r.toLowerCase() === "superadmin");

            if (fromLocation && !fromLocation.includes("/login")) {
                // If student trying to go to /admin, send to student dashboard instead
                if (!isSuperadmin && fromLocation.startsWith("/admin")) {
                    navigate("/student/dashboard", { replace: true });
                } else if (isSuperadmin && fromLocation.startsWith("/student")) {
                    navigate("/admin/dashboard", { replace: true });
                } else {
                    navigate(fromLocation, { replace: true });
                }
            } else if (isSuperadmin) {
                navigate("/admin/dashboard", { replace: true });
            } else {
                navigate("/student/dashboard", { replace: true });
            }
        } catch (err) {
            setApiError(parseApiError(err));
        } finally {
            setIsLoading(false);
        }
    };

    const emailErrors = apiError?.fields?.email;
    const passwordErrors = apiError?.fields?.password;

    return (
        <form
            onSubmit={handleSubmit}
            className="w-full max-w-md space-y-6"
            noValidate
            aria-label="Login form"
        >
            {apiError && !emailErrors && !passwordErrors && (
                <div
                    role="alert"
                    aria-live="polite"
                    className="p-3 text-sm rounded-md bg-red-50 border border-red-200 text-danger"
                >
                    <p className="font-medium">{apiError.message}</p>
                </div>
            )}

            <div className="space-y-1.5">
                <label
                    htmlFor="email"
                    className="block text-sm font-medium text-foreground"
                >
                    Email address
                </label>
                <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    aria-invalid={Boolean(emailErrors)}
                    aria-describedby={emailErrors ? "email-error" : undefined}
                    placeholder="learner@example.com"
                    className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                        emailErrors
                            ? "border-danger focus:ring-danger"
                            : "border-border hover:border-border-strong focus:ring-primary-500"
                    } disabled:opacity-50 disabled:bg-neutral-100`}
                />
                {emailErrors && (
                    <p id="email-error" className="text-xs text-danger">
                        {emailErrors.join(" ")}
                    </p>
                )}
            </div>

            <div className="space-y-1.5">
                <label
                    htmlFor="password"
                    className="block text-sm font-medium text-foreground"
                >
                    Password
                </label>
                <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    aria-invalid={Boolean(passwordErrors)}
                    aria-describedby={passwordErrors ? "password-error" : undefined}
                    placeholder="••••••••"
                    className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                        passwordErrors
                            ? "border-danger focus:ring-danger"
                            : "border-border hover:border-border-strong focus:ring-primary-500"
                    } disabled:opacity-50 disabled:bg-neutral-100`}
                />
                {passwordErrors && (
                    <p id="password-error" className="text-xs text-danger">
                        {passwordErrors.join(" ")}
                    </p>
                )}
            </div>

            <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={isLoading}
                disabled={isLoading || !email.trim() || !password}
                className="w-full"
            >
                {isLoading ? "Signing in..." : "Sign in"}
            </Button>
        </form>
    );
}
