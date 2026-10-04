import { useState } from "react";

import { Modal } from "@/shared/ui/Modal";
import { Button } from "@/shared/ui/Button";

export interface DeleteConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => Promise<void>;
    resourceName: string;
    resourceType: "Domain" | "Subject" | "Chapter" | "Topic";
    errorMessage?: string | null;
}

export function DeleteConfirmModal({
    isOpen,
    onClose,
    onConfirm,
    resourceName,
    resourceType,
    errorMessage,
}: DeleteConfirmModalProps) {
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDelete = async () => {
        setIsDeleting(true);
        try {
            await onConfirm();
            onClose();
        } catch {
            // Handled by parent or displayed via errorMessage
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Delete ${resourceType}`}
            description={`Are you sure you want to delete this ${resourceType.toLowerCase()}?`}
            maxWidth="md"
        >
            <div className="space-y-4">
                <p className="text-sm text-foreground">
                    You are about to delete{" "}
                    <span className="font-semibold text-foreground">
                        &ldquo;{resourceName}&rdquo;
                    </span>
                    . This action cannot be undone.
                </p>

                {errorMessage && (
                    <div
                        role="alert"
                        aria-live="polite"
                        className="p-3 rounded-md bg-red-50 border border-red-200 text-danger text-sm"
                    >
                        <p className="font-medium">{errorMessage}</p>
                    </div>
                )}

                <div className="flex items-center justify-end space-x-3 pt-2">
                    <Button
                        type="button"
                        variant="secondary"
                        onClick={onClose}
                        disabled={isDeleting}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="button"
                        variant="danger"
                        loading={isDeleting}
                        disabled={isDeleting}
                        onClick={handleDelete}
                    >
                        {isDeleting ? "Deleting..." : `Delete ${resourceType}`}
                    </Button>
                </div>
            </div>
        </Modal>
    );
}
