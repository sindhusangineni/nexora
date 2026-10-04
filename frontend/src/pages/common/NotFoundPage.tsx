import { Link } from "react-router-dom";

import { Button } from "@/shared/ui/Button";

export function NotFoundPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center space-y-4">
            <h1 className="text-4xl font-extrabold text-foreground tracking-tight">404</h1>
            <p className="text-lg font-medium text-foreground">Page not found</p>
            <p className="text-sm text-foreground-muted max-w-md">
                The page you are looking for does not exist or has been moved.
            </p>
            <div className="pt-2">
                <Link to="/">
                    <Button variant="primary" size="md">
                        Return home
                    </Button>
                </Link>
            </div>
        </div>
    );
}
