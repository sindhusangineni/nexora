import { LoginForm } from "@/features/auth";

export function LoginPage() {
    return (
        <div className="w-full max-w-md p-8 space-y-6 bg-surface rounded-xl border border-border shadow-sm">
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                    Sign in to Nexora
                </h1>
                <p className="text-sm text-foreground-muted">
                    Enter your email and password to access your platform account
                </p>
            </div>

            <LoginForm />
        </div>
    );
}
