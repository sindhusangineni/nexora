import React, { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Modal } from "@/shared/ui/Modal";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useCreateSection, useDeleteSection } from "../hooks/useAssessment";
import type { AssessmentSection } from "../types/assessment.types";

interface SectionManagerProps {
    assessmentId: string;
    sections: AssessmentSection[];
    isDraft: boolean;
}

export const SectionManager: React.FC<SectionManagerProps> = ({
    assessmentId,
    sections,
    isDraft,
}) => {
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [position, setPosition] = useState<number>(sections.length);
    const [error, setError] = useState<string | null>(null);

    const [deleteSectionId, setDeleteSectionId] = useState<string | null>(null);

    const createSectionMutation = useCreateSection(assessmentId);
    const deleteSectionMutation = useDeleteSection(assessmentId);

    const handleOpenAddModal = () => {
        setTitle("");
        setDescription("");
        setPosition(sections.length);
        setError(null);
        setIsAddModalOpen(true);
    };

    const handleCreateSection = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!title.trim()) {
            setError("Section title is required.");
            return;
        }

        try {
            await createSectionMutation.mutateAsync({
                title: title.trim(),
                description: description.trim(),
                position,
            });
            setIsAddModalOpen(false);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to create section.";
            setError(message);
        }
    };

    const handleDeleteSection = async () => {
        if (!deleteSectionId) return;
        try {
            await deleteSectionMutation.mutateAsync(deleteSectionId);
            setDeleteSectionId(null);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to delete section.";
            setError(message);
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-sm font-semibold text-foreground tracking-tight">
                        Assessment Sections
                    </h3>
                    <p className="text-xs text-foreground-muted mt-0.5">
                        Divide questions into structured sections (e.g. General Studies, Current Affairs).
                    </p>
                </div>
                {isDraft && (
                    <Button
                        size="sm"
                        variant="secondary"
                        onClick={handleOpenAddModal}
                        aria-label="Add Section"
                    >
                        + Add Section
                    </Button>
                )}
            </div>

            {sections.length === 0 ? (
                <EmptyState
                    title="No Sections Defined"
                    description={
                        isDraft
                            ? "Optional: You can create sections to group questions into logical segments with distinct presentation orders."
                            : "This assessment has no sections; questions will be presented at the assessment level."
                    }
                    action={
                        isDraft ? (
                            <Button
                                size="sm"
                                variant="secondary"
                                onClick={handleOpenAddModal}
                            >
                                Create First Section
                            </Button>
                        ) : undefined
                    }
                />
            ) : (
                <div className="space-y-2">
                    {sections.map((sec, idx) => (
                        <div
                            key={sec.id}
                            className="flex items-center justify-between p-3.5 bg-surface border border-border rounded-lg shadow-2xs hover:border-neutral-300 transition-colors"
                        >
                            <div className="flex items-start space-x-3">
                                <span className="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-full bg-neutral-100 text-neutral-800 text-xs font-semibold">
                                    {sec.position + 1}
                                </span>
                                <div>
                                    <h4 className="text-sm font-medium text-foreground">
                                        {sec.title}
                                    </h4>
                                    {sec.description && (
                                        <p className="text-xs text-foreground-muted mt-0.5">
                                            {sec.description}
                                        </p>
                                    )}
                                    <span className="text-[11px] text-neutral-400 mt-1 block">
                                        Position: {sec.position} (Order #{idx + 1})
                                    </span>
                                </div>
                            </div>

                            {isDraft && (
                                <Button
                                    variant="danger"
                                    size="sm"
                                    onClick={() => setDeleteSectionId(sec.id)}
                                    aria-label={`Delete section ${sec.title}`}
                                >
                                    Delete
                                </Button>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Add Section Modal */}
            <Modal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                title="Add Assessment Section"
            >
                <form onSubmit={handleCreateSection} className="space-y-4">
                    {error && (
                        <div className="p-3 text-xs text-danger bg-danger-surface rounded-md border border-danger/20">
                            {error}
                        </div>
                    )}

                    <Input
                        label="Section Title"
                        required
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. General Studies Paper I"
                        autoFocus
                    />

                    <div>
                        <label
                            htmlFor="section-desc"
                            className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                        >
                            Description (Optional)
                        </label>
                        <textarea
                            id="section-desc"
                            rows={3}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="w-full px-3 py-2 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            placeholder="Optional instructions or overview for this section..."
                        />
                    </div>

                    <div>
                        <Input
                            label="Position / Sequence Order"
                            type="number"
                            min={0}
                            required
                            value={position}
                            onChange={(e) => setPosition(parseInt(e.target.value, 10) || 0)}
                            helperText="Determines the presentation order of this section."
                        />
                    </div>

                    <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={() => setIsAddModalOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            variant="primary"
                            loading={createSectionMutation.isPending}
                        >
                            Add Section
                        </Button>
                    </div>
                </form>
            </Modal>

            {/* Delete Section Confirmation Modal */}
            <Modal
                isOpen={Boolean(deleteSectionId)}
                onClose={() => setDeleteSectionId(null)}
                title="Delete Assessment Section"
            >
                <div className="space-y-4">
                    <p className="text-sm text-foreground-muted">
                        Are you sure you want to delete this section? Any selection rules assigned to this section will have their section association removed or will need to be reconfigured.
                    </p>
                    <div className="flex justify-end space-x-2 pt-2 border-t border-border">
                        <Button
                            variant="secondary"
                            onClick={() => setDeleteSectionId(null)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="danger"
                            loading={deleteSectionMutation.isPending}
                            onClick={handleDeleteSection}
                        >
                            Confirm Delete
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};
