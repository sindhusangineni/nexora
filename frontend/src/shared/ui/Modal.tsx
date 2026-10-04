import { useEffect, useRef, type ReactNode } from "react";

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
    const dialogRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen) return;

        // Prevent body scroll behind modal
        const originalOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                onClose();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => {
            document.body.style.overflow = originalOverflow;
            window.removeEventListener("keydown", handleKeyDown);
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-2 sm:p-4 bg-neutral-900/60 backdrop-blur-xs animate-in fade-in duration-150"
            onClick={onClose}
        >
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
                aria-describedby={description ? "modal-description" : undefined}
                className={`w-full ${maxWidthStyles[maxWidth]} max-h-[calc(100dvh-2rem)] flex flex-col bg-surface rounded-t-2xl sm:rounded-xl border border-border shadow-xl p-5 sm:p-6 space-y-4 animate-in slide-in-from-bottom-3 sm:zoom-in-95 duration-150`}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-start justify-between gap-3 shrink-0">
                    <div className="min-w-0 flex-1">
                        <h2
                            id="modal-title"
                            className="text-base sm:text-lg font-semibold text-foreground tracking-tight truncate"
                        >
                            {title}
                        </h2>
                        {description && (
                            <p
                                id="modal-description"
                                className="text-xs text-foreground-muted mt-0.5 line-clamp-2"
                            >
                                {description}
                            </p>
                        )}
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close dialog"
                        className="text-foreground-muted hover:text-foreground -mr-2 -mt-2 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg hover:bg-neutral-100 transition-colors cursor-pointer shrink-0"
                    >
                        <span aria-hidden="true" className="text-xl leading-none">
                            &times;
                        </span>
                    </button>
                </div>

                <div className="overflow-y-auto max-h-[70vh] sm:max-h-[75vh] pr-0.5">
                    {children}
                </div>
            </div>
        </div>
    );
}
