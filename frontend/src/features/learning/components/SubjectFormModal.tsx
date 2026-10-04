import { useState, type FormEvent } from "react";

import { Modal } from "@/shared/ui/Modal";
import { Button } from "@/shared/ui/Button";
import { parseApiError, type ApiError } from "@/lib/api";
import type { Subject } from "../types/learning.types";

export interface SubjectFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    domainId: string;
    domainName: string;
    initialData?: Subject | null;
    onSubmit: (data: {
        domain: string;
        name: string;
        description: string;
        position: number;
    }) => Promise<void>;
}

function SubjectFormContent({
    onClose,
    domainId,
    domainName,
    initialData,
    onSubmit,
}: Omit<SubjectFormModalProps, "isOpen">) {
    const isEdit = Boolean(initialData);
    const [name, setName] = useState(initialData?.name || "");
    const [description, setDescription] = useState(initialData?.description || "");
    const [position, setPosition] = useState(initialData?.position ?? 0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [apiError, setApiError] = useState<ApiError | null>(null);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        const cleanName = name.trim();
        if (!cleanName) return;

        setIsSubmitting(true);
        setApiError(null);
        try {
            await onSubmit({
                domain: domainId,
                name: cleanName,
                description: description.trim(),
                position: Number(position) || 0,
            });
            onClose();
        } catch (err) {
            setApiError(parseApiError(err));
        } finally {
            setIsSubmitting(false);
        }
    };

    const nameErrors = apiError?.fields?.name;
    const descErrors = apiError?.fields?.description;
    const posErrors = apiError?.fields?.position;

    return (
        <Modal
            isOpen={true}
            onClose={onClose}
            title={isEdit ? "Edit Subject" : "Create New Subject"}
            description={`Parent Domain: ${domainName}`}
        >
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                {apiError && !nameErrors && !descErrors && !posErrors && (
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
                        htmlFor="subject-name"
                        className="block text-sm font-medium text-foreground"
                    >
                        Subject Name <span className="text-danger">*</span>
                    </label>
                    <input
                        id="subject-name"
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(nameErrors)}
                        aria-describedby={nameErrors ? "subject-name-error" : undefined}
                        placeholder="e.g. Modern Indian History"
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            nameErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {nameErrors && (
                        <p id="subject-name-error" className="text-xs text-danger">
                            {nameErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="subject-position"
                        className="block text-sm font-medium text-foreground"
                    >
                        Display Order / Position
                    </label>
                    <input
                        id="subject-position"
                        type="number"
                        min={0}
                        value={position}
                        onChange={(e) => setPosition(parseInt(e.target.value, 10) || 0)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(posErrors)}
                        aria-describedby={posErrors ? "subject-pos-error" : undefined}
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            posErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {posErrors && (
                        <p id="subject-pos-error" className="text-xs text-danger">
                            {posErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="subject-description"
                        className="block text-sm font-medium text-foreground"
                    >
                        Description
                    </label>
                    <textarea
                        id="subject-description"
                        rows={3}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(descErrors)}
                        aria-describedby={descErrors ? "subject-desc-error" : undefined}
                        placeholder="Subject overview and scope"
                        className={`w-full p-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            descErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {descErrors && (
                        <p id="subject-desc-error" className="text-xs text-danger">
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
                        {isEdit ? "Save Changes" : "Create Subject"}
                    </Button>
                </div>
            </form>
        </Modal>
    );
}

export function SubjectFormModal(props: SubjectFormModalProps) {
    if (!props.isOpen) return null;
    return (
        <SubjectFormContent
            key={props.initialData?.id || "create"}
            onClose={props.onClose}
            domainId={props.domainId}
            domainName={props.domainName}
            initialData={props.initialData}
            onSubmit={props.onSubmit}
        />
    );
}
