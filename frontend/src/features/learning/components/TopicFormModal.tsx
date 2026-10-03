import { useState, type FormEvent } from "react";

import { Modal } from "@/shared/ui/Modal";
import { Button } from "@/shared/ui/Button";
import { parseApiError, type ApiError } from "@/lib/api";
import type { Topic } from "../types/learning.types";

export interface TopicFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    chapterId: string;
    chapterName: string;
    initialData?: Topic | null;
    onSubmit: (data: {
        chapter: string;
        name: string;
        description: string;
        position: number;
    }) => Promise<void>;
}

function TopicFormContent({
    onClose,
    chapterId,
    chapterName,
    initialData,
    onSubmit,
}: Omit<TopicFormModalProps, "isOpen">) {
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
                chapter: chapterId,
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
            title={isEdit ? "Edit Topic" : "Create New Topic"}
            description={`Parent Chapter: ${chapterName}`}
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
                        htmlFor="topic-name"
                        className="block text-sm font-medium text-foreground"
                    >
                        Topic Name <span className="text-danger">*</span>
                    </label>
                    <input
                        id="topic-name"
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(nameErrors)}
                        aria-describedby={nameErrors ? "topic-name-error" : undefined}
                        placeholder="e.g. Non-Cooperation Movement"
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            nameErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {nameErrors && (
                        <p id="topic-name-error" className="text-xs text-danger">
                            {nameErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="topic-position"
                        className="block text-sm font-medium text-foreground"
                    >
                        Display Order / Position
                    </label>
                    <input
                        id="topic-position"
                        type="number"
                        min={0}
                        value={position}
                        onChange={(e) => setPosition(parseInt(e.target.value, 10) || 0)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(posErrors)}
                        aria-describedby={posErrors ? "topic-pos-error" : undefined}
                        className={`w-full h-10 px-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            posErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {posErrors && (
                        <p id="topic-pos-error" className="text-xs text-danger">
                            {posErrors.join(" ")}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <label
                        htmlFor="topic-description"
                        className="block text-sm font-medium text-foreground"
                    >
                        Description
                    </label>
                    <textarea
                        id="topic-description"
                        rows={3}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={isSubmitting}
                        aria-invalid={Boolean(descErrors)}
                        aria-describedby={descErrors ? "topic-desc-error" : undefined}
                        placeholder="Learning objectives and core concepts"
                        className={`w-full p-3 text-sm rounded-md border bg-surface text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            descErrors
                                ? "border-danger focus:ring-danger"
                                : "border-border hover:border-border-strong focus:ring-primary-500"
                        } disabled:opacity-50`}
                    />
                    {descErrors && (
                        <p id="topic-desc-error" className="text-xs text-danger">
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
                        {isEdit ? "Save Changes" : "Create Topic"}
                    </Button>
                </div>
            </form>
        </Modal>
    );
}

export function TopicFormModal(props: TopicFormModalProps) {
    if (!props.isOpen) return null;
    return (
        <TopicFormContent
            key={props.initialData?.id || "create"}
            onClose={props.onClose}
            chapterId={props.chapterId}
            chapterName={props.chapterName}
            initialData={props.initialData}
            onSubmit={props.onSubmit}
        />
    );
}
