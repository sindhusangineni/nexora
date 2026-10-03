export interface PlaceholderPageProps {
    title: string;
    description?: string;
}

export function PlaceholderPage({
    title,
    description = "This feature area is currently under active development.",
}: PlaceholderPageProps) {
    return (
        <div className="space-y-4">
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                    {title}
                </h1>
                <p className="text-sm text-foreground-muted mt-1">{description}</p>
            </div>

            <div className="p-12 text-center border border-dashed rounded-lg border-border bg-surface-muted">
                <p className="text-sm font-medium text-foreground-muted">
                    Module integration in progress.
                </p>
            </div>
        </div>
    );
}
