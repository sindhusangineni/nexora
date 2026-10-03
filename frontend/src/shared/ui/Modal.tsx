import { useEffect, type ReactNode } from "react";

export interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    description?: string;
    children: ReactNode;
    maxWidth?: "sm" | "md" | "lg" | "xl";
}

const maxWidthStyles = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
};

export function Modal({
    isOpen,
    onClose,
    title,
    description,
    children,
    maxWidth = "md",
}: ModalProps) {
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                onClose();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-neutral-900/50 backdrop-blur-xs animate-in fade-in duration-150"
            onClick={onClose}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
                aria-describedby={description ? "modal-description" : undefined}
                className={`w-full ${maxWidthStyles[maxWidth]} bg-surface rounded-xl border border-border shadow-lg p-6 space-y-4`}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-start justify-between">
                    <div>
                        <h2
                            id="modal-title"
                            className="text-lg font-semibold text-foreground tracking-tight"
                        >
                            {title}
                        </h2>
                        {description && (
                            <p
                                id="modal-description"
                                className="text-xs text-foreground-muted mt-0.5"
                            >
                                {description}
                            </p>
                        )}
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close dialog"
                        className="text-foreground-muted hover:text-foreground p-1 rounded-md hover:bg-neutral-100 transition-colors cursor-pointer"
                    >
                        <span aria-hidden="true" className="text-xl leading-none">
                            &times;
                        </span>
                    </button>
                </div>

                <div>{children}</div>
            </div>
        </div>
    );
}
