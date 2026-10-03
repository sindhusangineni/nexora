export interface LoadingScreenProps {
    message?: string;
}

export function LoadingScreen({ message = "Loading..." }: LoadingScreenProps) {
    return (
        <div
            role="status"
            aria-live="polite"
            className="flex flex-col items-center justify-center min-h-[50vh] p-6 space-y-4"
        >
            <div className="w-10 h-10 border-4 rounded-full border-primary-200 border-t-primary-600 animate-spin" />
            <p className="text-sm font-medium text-foreground-muted">{message}</p>
        </div>
    );
}
