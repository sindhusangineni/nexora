import { useState, type FormEvent } from "react";

import { Modal } from "@/shared/ui/Modal";
import { Button } from "@/shared/ui/Button";
import { parseApiError, type ApiError } from "@/lib/api";
import type { Domain } from "../types/learning.types";

export interface DomainFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialData?: Domain | null;
    onSubmit: (data: { name: string; description: string }) => Promise<void>;
}

function DomainFormContent({
    onClose,
    initialData,
    onSubmit,
}: Omit<DomainFormModalProps, "isOpen">) {
    const isEdit = Boolean(initialData);
    const [name, setName] = useState(initialData?.name || "");
    const [description, setDescription] = useState(initialData?.description || "");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [apiError, setApiError] = useState<ApiError | null>(null);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        const cleanName = name.trim();
        if (!cleanName) return;

        setIsSubmitting(true);
        setApiError(null);
        try {
            await onSubmit({ name: cleanName, description: description.trim() });
            onClose();
        } catch (err) {
            setApiError(parseApiError(err));
        } finally {
            setIsSubmitting(false);
        }
    };

    const nameErrors = apiError?.fields?.name;
    const descErrors = apiError?.fields?.description;

    return (
        <Modal
            isOpen={true}
            onClose={onClose}
            title={isEdit ? "Edit Domain" : "Create New Domain"}
            description={
                isEdit
                    ? "Update the curriculum domain details."
                    : "Add a top-level curriculum domain (e.g., UPSC, Engineering)."
            }
        >
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                {apiError && !nameErrors && !descErrors && (
                    <div
                        role="alert"
                        aria-live="polite"
                        className="p-3 text-sm rounded-md bg-red-50 border border-red-200 text-danger font-medium"
                    >
                        {apiError.message}
                    </div>
                )}

                <div className="space-y-1.5">
                    <label
                        htmlFor="domain-name"
                        className="block text-sm font-medium text-foreground"
                    >
                        Domain Name <span className="text-danger">*</span>
                    </label>
                    <input
                        id="domain-name"
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(nameErrors)}
                        aria-describedby={nameErrors ? "domain-name-error" : undefined}
                        placeholder="e.g. UPSC Civil Services"
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            nameErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {nameErrors && (
                        <p id="domain-name-error" className="text-xs text-danger">
                            {nameErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="domain-description"
                        className="block text-sm font-medium text-foreground"
                    >
                        Description
                    </label>
                    <textarea
                        id="domain-description"
                        rows={3}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(descErrors)}
                        aria-describedby={descErrors ? "domain-desc-error" : undefined}
                        placeholder="Optional curriculum overview and syllabus notes"
                        className={`w-full p-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            descErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {descErrors && (
                        <p id="domain-desc-error" className="text-xs text-danger">
                            {descErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="flex items-center justify-end space-x-3 pt-2">
                    <Button
                        type="button"
                        variant="secondary"
                        onClick={onClose}
                        disabled={isSubmitting}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="primary"
                        loading={isSubmitting}
                        disabled={isSubmitting || !name.trim()}
                    >
                        {isEdit ? "Save Changes" : "Create Domain"}
                    </Button>
                </div>
            </form>
        </Modal>
    );
}

export function DomainFormModal(props: DomainFormModalProps) {
    if (!props.isOpen) return null;
    return (
        <DomainFormContent
            key={props.initialData?.id || "create"}
            onClose={props.onClose}
            initialData={props.initialData}
            onSubmit={props.onSubmit}
        />
    );
}
