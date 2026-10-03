import { useState, type FormEvent } from "react";

import { Modal } from "@/shared/ui/Modal";
import { Button } from "@/shared/ui/Button";
import { parseApiError, type ApiError } from "@/lib/api";
import type { Chapter } from "../types/learning.types";

export interface ChapterFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    subjectId: string;
    subjectName: string;
    initialData?: Chapter | null;
    onSubmit: (data: {
        subject: string;
        name: string;
        description: string;
        position: number;
    }) => Promise<void>;
}

function ChapterFormContent({
    onClose,
    subjectId,
    subjectName,
    initialData,
    onSubmit,
}: Omit<ChapterFormModalProps, "isOpen">) {
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
                subject: subjectId,
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
            title={isEdit ? "Edit Chapter" : "Create New Chapter"}
            description={`Parent Subject: ${subjectName}`}
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
                        htmlFor="chapter-name"
                        className="block text-sm font-medium text-foreground"
                    >
                        Chapter Name <span className="text-danger">*</span>
                    </label>
                    <input
                        id="chapter-name"
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(nameErrors)}
                        aria-describedby={nameErrors ? "chapter-name-error" : undefined}
                        placeholder="e.g. Freedom Struggle (1857-1947)"
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            nameErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {nameErrors && (
                        <p id="chapter-name-error" className="text-xs text-danger">
                            {nameErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="chapter-position"
                        className="block text-sm font-medium text-foreground"
                    >
                        Display Order / Position
                    </label>
                    <input
                        id="chapter-position"
                        type="number"
                        min={0}
                        value={position}
                        onChange={(e) => setPosition(parseInt(e.target.value, 10) || 0)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(posErrors)}
                        aria-describedby={posErrors ? "chapter-pos-error" : undefined}
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            posErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {posErrors && (
                        <p id="chapter-pos-error" className="text-xs text-danger">
                            {posErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="chapter-description"
                        className="block text-sm font-medium text-foreground"
                    >
                        Description
                    </label>
                    <textarea
                        id="chapter-description"
                        rows={3}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(descErrors)}
                        aria-describedby={descErrors ? "chapter-desc-error" : undefined}
                        placeholder="Chapter syllabus coverage"
                        className={`w-full p-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            descErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {descErrors && (
                        <p id="chapter-desc-error" className="text-xs text-danger">
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
                        {isEdit ? "Save Changes" : "Create Chapter"}
                    </Button>
                </div>
            </form>
        </Modal>
    );
}

export function ChapterFormModal(props: ChapterFormModalProps) {
    if (!props.isOpen) return null;
    return (
        <ChapterFormContent
            key={props.initialData?.id || "create"}
            onClose={props.onClose}
            subjectId={props.subjectId}
            subjectName={props.subjectName}
            initialData={props.initialData}
            onSubmit={props.onSubmit}
        />
    );
}
