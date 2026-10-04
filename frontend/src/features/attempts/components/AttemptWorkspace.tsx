import React, { useState, useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { BrandLogo } from "@/shared/ui/BrandLogo";
import { AttemptStatusBadge } from "./AttemptStatusBadge";
import { AttemptTimer } from "./AttemptTimer";
import { AttemptProgress } from "./AttemptProgress";
import { QuestionNavigator } from "./QuestionNavigator";
import { AttemptQuestion } from "./AttemptQuestion";
import { SubmitAttemptModal } from "./SubmitAttemptModal";
import type { SaveStatus } from "./ResponseSaveIndicator";
import { useDeliveryQuestion } from "../hooks/useAttempts";
import type {
    AttemptDelivery,
    SaveResponsePayload,
} from "../types/attempt.types";
import type {
    Assessment,
    AssessmentPaper,
    AssessmentSection,
} from "@/features/assessment/types/assessment.types";
import { LockIcon, MenuIcon, CloseIcon, AlertTriangleIcon } from "./Icons";

interface AttemptWorkspaceProps {
    attempt: AttemptDelivery;
    assessment?: Assessment;
    sections?: AssessmentSection[];
    paper?: AssessmentPaper;
    onSaveResponse: (itemId: string, payload: SaveResponsePayload) => Promise<void>;
    onClearResponse: (itemId: string) => Promise<void>;
    onSubmitAttempt: () => Promise<void>;
    onExpireReconcile?: () => void;
    isSubmitting?: boolean;
}

export const AttemptWorkspace: React.FC<AttemptWorkspaceProps> = ({
    attempt,
    assessment,
    sections = [],
    paper,
    onSaveResponse,
    onClearResponse,
    onSubmitAttempt,
    onExpireReconcile,
    isSubmitting = false,
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [isMobileNavigatorOpen, setIsMobileNavigatorOpen] = useState(false);
    const [itemSaveStatus, setItemSaveStatus] = useState<Record<string, SaveStatus>>({});
    const [itemSaveError, setItemSaveError] = useState<Record<string, string>>({});
    const [hasExpired, setHasExpired] = useState(false);

    const items = attempt.items || [];
    const totalCount = items.length;
    const currentItem = items[currentIndex];

    // Map paper_item_id to paper item to get question_id & question_version_id
    const paperItemMap = new Map();
    paper?.items?.forEach((pi) => paperItemMap.set(pi.id, pi));

    const matchedPaperItem = currentItem ? paperItemMap.get(currentItem.paper_item_id) : null;
    const questionId = matchedPaperItem?.question_id;
    const questionVersionId = matchedPaperItem?.question_version_id;

    // Fetch sanitized question content for the current item
    const { data: questionVersion } = useDeliveryQuestion(questionId, questionVersionId);

    // Section title
    const sectionTitle = sections.find(
        (s) => s.id === currentItem?.assessment_section_id,
    )?.title;

    // Answered count calculation
    const answeredCount = items.filter(
        (i) => i.response?.answer_state === "ANSWERED",
    ).length;

    const isReadOnly = attempt.status !== "IN_PROGRESS" || hasExpired;

    // Warn on accidental tab close while in progress
    useEffect(() => {
        if (isReadOnly) return;

        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            e.preventDefault();
            e.returnValue = "";
        };

        window.addEventListener("beforeunload", handleBeforeUnload);
        return () => window.removeEventListener("beforeunload", handleBeforeUnload);
    }, [isReadOnly]);

    // Close mobile navigator on Escape
    useEffect(() => {
        if (!isMobileNavigatorOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                setIsMobileNavigatorOpen(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isMobileNavigatorOpen]);

    // Handle timer expiration
    const handleTimerExpire = () => {
        setHasExpired(true);
        onExpireReconcile?.();
    };

    // Save response handler
    const handleSave = async (payload: SaveResponsePayload) => {
        if (!currentItem || isReadOnly) return;

        const itemId = currentItem.id;
        setItemSaveStatus((prev) => ({ ...prev, [itemId]: "saving" }));
        setItemSaveError((prev) => ({ ...prev, [itemId]: "" }));

        try {
            await onSaveResponse(itemId, payload);
            setItemSaveStatus((prev) => ({ ...prev, [itemId]: "saved" }));
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to save response";
            if (msg.includes("expired") || msg.includes("409")) {
                setHasExpired(true);
                onExpireReconcile?.();
            }
            setItemSaveStatus((prev) => ({ ...prev, [itemId]: "error" }));
            setItemSaveError((prev) => ({ ...prev, [itemId]: msg }));
        }
    };

    // Clear response handler
    const handleClear = async () => {
        if (!currentItem || isReadOnly) return;

        const itemId = currentItem.id;
        setItemSaveStatus((prev) => ({ ...prev, [itemId]: "saving" }));

        try {
            await onClearResponse(itemId);
            setItemSaveStatus((prev) => ({ ...prev, [itemId]: "idle" }));
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to clear response";
            setItemSaveStatus((prev) => ({ ...prev, [itemId]: "error" }));
            setItemSaveError((prev) => ({ ...prev, [itemId]: msg }));
        }
    };

    const handleNext = () => {
        if (currentIndex < totalCount - 1) {
            setCurrentIndex((prev) => prev + 1);
        }
    };

    const handlePrevious = () => {
        if (currentIndex > 0) {
            setCurrentIndex((prev) => prev - 1);
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Top Workspace Header */}
            <header className="sticky top-0 z-30 bg-surface/95 backdrop-blur-xs border-b border-border shadow-2xs">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
                    <div className="flex items-center space-x-3 overflow-hidden">
                        <BrandLogo />
                        <span className="text-border">|</span>
                        <div className="truncate">
                            <span className="text-xs font-semibold text-neutral-900 block truncate">
                                {assessment?.title || "Assessment Session"}
                            </span>
                            <span className="text-[11px] text-foreground-muted">
                                Attempt #{attempt.attempt_number}
                            </span>
                        </div>
                        <AttemptStatusBadge status={attempt.status} className="hidden sm:inline-flex" />
                    </div>

                    <div className="flex items-center space-x-3 shrink-0">
                        {attempt.status === "IN_PROGRESS" && (
                            <AttemptTimer
                                expiresAt={attempt.expires_at}
                                onExpire={handleTimerExpire}
                            />
                        )}

                        <Button
                            type="button"
                            variant="primary"
                            size="sm"
                            onClick={() => setIsSubmitModalOpen(true)}
                            disabled={isReadOnly || isSubmitting}
                        >
                            {isSubmitting ? "Submitting..." : "Submit Test"}
                        </Button>

                        {/* Mobile Navigator Toggle */}
                        <button
                            type="button"
                            onClick={() => setIsMobileNavigatorOpen((prev) => !prev)}
                            className="lg:hidden min-w-[44px] min-h-[44px] flex items-center justify-center p-2 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-md cursor-pointer"
                            aria-label="Toggle Question Navigator"
                        >
                            {isMobileNavigatorOpen ? (
                                <CloseIcon className="w-5 h-5" />
                            ) : (
                                <MenuIcon className="w-5 h-5" />
                            )}
                        </button>
                    </div>
                </div>
            </header>

            {/* Read-only / Expired Warning Banner */}
            {isReadOnly && (
                <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-xs text-amber-900 flex items-center justify-center space-x-2">
                    {hasExpired ? (
                        <>
                            <AlertTriangleIcon className="w-4 h-4 text-amber-700 shrink-0" />
                            <span>
                                <strong>Attempt Expired:</strong> Your time limit has expired and answers have been submitted. Editing is disabled.
                            </span>
                        </>
                    ) : (
                        <>
                            <LockIcon className="w-4 h-4 text-amber-700 shrink-0" />
                            <span>
                                <strong>Read-Only Session:</strong> This attempt has status <strong>{attempt.status}</strong>. Responses can no longer be modified.
                            </span>
                        </>
                    )}
                </div>
            )}

            {/* Main Workspace Body */}
            <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                    {/* Left Question Pane (8 cols on desktop) */}
                    <div className="lg:col-span-8 space-y-4">
                        {currentItem ? (
                            <Card className="p-6 sm:p-8 shadow-xs">
                                <AttemptQuestion
                                    key={currentItem.id}
                                    item={currentItem}
                                    questionVersion={questionVersion}
                                    index={currentIndex}
                                    totalCount={totalCount}
                                    sectionTitle={sectionTitle}
                                    saveStatus={itemSaveStatus[currentItem.id] || "idle"}
                                    saveErrorMessage={itemSaveError[currentItem.id]}
                                    onSave={handleSave}
                                    onClear={handleClear}
                                    onPrevious={handlePrevious}
                                    onNext={handleNext}
                                    hasPrevious={currentIndex > 0}
                                    hasNext={currentIndex < totalCount - 1}
                                    disabled={isReadOnly}
                                />
                            </Card>
                        ) : (
                            <Card className="p-8 text-center text-xs text-foreground-muted">
                                No questions found in this assessment paper.
                            </Card>
                        )}
                    </div>

                    {/* Right Question Navigator & Progress Pane (4 cols on desktop) */}
                    <aside
                        className={`lg:col-span-4 space-y-5 ${
                            isMobileNavigatorOpen
                                ? "fixed inset-0 top-16 z-20 bg-background/95 p-4 overflow-y-auto block"
                                : "hidden lg:block"
                        }`}
                    >
                        <Card className="p-5 space-y-5">
                            <AttemptProgress
                                answeredCount={answeredCount}
                                totalCount={totalCount}
                            />

                            <QuestionNavigator
                                items={items}
                                currentIndex={currentIndex}
                                onSelectIndex={(idx) => {
                                    setCurrentIndex(idx);
                                    setIsMobileNavigatorOpen(false);
                                }}
                                sections={sections}
                            />
                        </Card>
                    </aside>
                </div>
            </main>

            {/* Submit Confirmation Modal */}
            <SubmitAttemptModal
                isOpen={isSubmitModalOpen}
                onClose={() => setIsSubmitModalOpen(false)}
                onConfirm={async () => {
                    setIsSubmitModalOpen(false);
                    await onSubmitAttempt();
                }}
                totalQuestions={totalCount}
                answeredQuestions={answeredCount}
                isSubmitting={isSubmitting}
            />
        </div>
    );
};
