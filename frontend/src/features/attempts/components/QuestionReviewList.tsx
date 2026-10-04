import React, { useState, useMemo } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { FilterIcon } from "./Icons";
import { QuestionReviewItem } from "./QuestionReviewItem";
import type { StudentQuestionReviewItem } from "../types/attempt.types";

interface QuestionReviewListProps {
    items: StudentQuestionReviewItem[];
    isFinalized: boolean;
}

type ReviewFilter = "ALL" | "CORRECT" | "INCORRECT" | "PARTIALLY_CORRECT" | "UNATTEMPTED" | "PENDING";

export const QuestionReviewList: React.FC<QuestionReviewListProps> = ({
    items,
    isFinalized,
}) => {
    const [activeFilter, setActiveFilter] = useState<ReviewFilter>("ALL");
    const [selectedSection, setSelectedSection] = useState<string>("ALL");

    // Extract unique sections
    const sections = useMemo(() => {
        const secSet = new Set<string>();
        items.forEach((item) => {
            if (item.section_name) {
                secSet.add(item.section_name);
            }
        });
        return Array.from(secSet);
    }, [items]);

    // Counts for filter pills
    const counts = useMemo(() => {
        let correct = 0;
        let incorrect = 0;
        let partiallyCorrect = 0;
        let unattempted = 0;
        let pending = 0;

        items.forEach((it) => {
            if (it.evaluation_status === "CORRECT") correct++;
            else if (it.evaluation_status === "INCORRECT") incorrect++;
            else if (it.evaluation_status === "PARTIALLY_CORRECT") partiallyCorrect++;
            else if (it.evaluation_status === "PENDING_EVALUATION") pending++;
            else if (it.evaluation_status === "UNATTEMPTED" || !it.is_answered) unattempted++;
        });

        return {
            ALL: items.length,
            CORRECT: correct,
            INCORRECT: incorrect,
            PARTIALLY_CORRECT: partiallyCorrect,
            UNATTEMPTED: unattempted,
            PENDING: pending,
        };
    }, [items]);

    // Filter items
    const filteredItems = useMemo(() => {
        return items.filter((item) => {
            // Section filter
            if (selectedSection !== "ALL" && item.section_name !== selectedSection) {
                return false;
            }

            // Status filter
            if (activeFilter === "ALL") return true;
            if (activeFilter === "CORRECT") return item.evaluation_status === "CORRECT";
            if (activeFilter === "INCORRECT") return item.evaluation_status === "INCORRECT";
            if (activeFilter === "PARTIALLY_CORRECT") return item.evaluation_status === "PARTIALLY_CORRECT";
            if (activeFilter === "PENDING") return item.evaluation_status === "PENDING_EVALUATION";
            if (activeFilter === "UNATTEMPTED") {
                return item.evaluation_status === "UNATTEMPTED" || !item.is_answered;
            }
            return true;
        });
    }, [items, activeFilter, selectedSection]);

    const scrollToQuestion = (questionNumber: number) => {
        const el = document.getElementById(`question-review-${questionNumber}`);
        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    };

    return (
        <div className="space-y-6">
            {/* Filter and Quick Navigator Header */}
            <Card className="p-5 border-border bg-surface space-y-4 shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3.5">
                    <div className="flex items-center space-x-2">
                        <FilterIcon className="w-4 h-4 text-primary" />
                        <h2 className="text-sm font-bold text-foreground tracking-tight">
                            Question-by-Question Review
                        </h2>
                    </div>

                    {/* Section Selector if multiple sections */}
                    {sections.length > 1 && (
                        <div className="flex items-center space-x-2">
                            <label htmlFor="review-section-select" className="text-xs text-foreground-muted font-medium">
                                Section:
                            </label>
                            <select
                                id="review-section-select"
                                value={selectedSection}
                                onChange={(e) => setSelectedSection(e.target.value)}
                                className="text-xs bg-surface border border-border rounded-md px-2.5 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                            >
                                <option value="ALL">All Sections</option>
                                {sections.map((s) => (
                                    <option key={s} value={s}>
                                        {s}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {/* Filter Tabs */}
                <div className="flex flex-wrap gap-2 text-xs">
                    <button
                        type="button"
                        onClick={() => setActiveFilter("ALL")}
                        className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                            activeFilter === "ALL"
                                ? "bg-primary text-white shadow-xs"
                                : "bg-surface-muted text-foreground-muted hover:text-foreground"
                        }`}
                    >
                        All ({counts.ALL})
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveFilter("CORRECT")}
                        className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                            activeFilter === "CORRECT"
                                ? "bg-emerald-600 text-white shadow-xs"
                                : "bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
                        }`}
                    >
                        Correct ({counts.CORRECT})
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveFilter("INCORRECT")}
                        className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                            activeFilter === "INCORRECT"
                                ? "bg-red-600 text-white shadow-xs"
                                : "bg-red-50 text-red-800 hover:bg-red-100"
                        }`}
                    >
                        Incorrect ({counts.INCORRECT})
                    </button>

                    {counts.PARTIALLY_CORRECT > 0 && (
                        <button
                            type="button"
                            onClick={() => setActiveFilter("PARTIALLY_CORRECT")}
                            className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                                activeFilter === "PARTIALLY_CORRECT"
                                ? "bg-amber-600 text-white shadow-xs"
                                : "bg-amber-50 text-amber-800 hover:bg-amber-100"
                            }`}
                        >
                            Partially Correct ({counts.PARTIALLY_CORRECT})
                        </button>
                    )}

                    {counts.PENDING > 0 && (
                        <button
                            type="button"
                            onClick={() => setActiveFilter("PENDING")}
                            className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                                activeFilter === "PENDING"
                                    ? "bg-amber-600 text-white shadow-xs"
                                    : "bg-amber-50 text-amber-800 hover:bg-amber-100"
                            }`}
                        >
                            Pending ({counts.PENDING})
                        </button>
                    )}

                    <button
                        type="button"
                        onClick={() => setActiveFilter("UNATTEMPTED")}
                        className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                            activeFilter === "UNATTEMPTED"
                                ? "bg-neutral-700 text-white shadow-xs"
                                : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                        }`}
                    >
                        Unanswered ({counts.UNATTEMPTED})
                    </button>
                </div>

                {/* Quick Question Number Matrix */}
                <div className="pt-2 border-t border-border">
                    <span className="text-[11px] font-semibold text-foreground-muted uppercase tracking-wider block mb-2">
                        Jump to Question
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                        {items.map((it) => {
                            let dotStyle = "bg-neutral-100 text-neutral-700 border-neutral-200 hover:border-neutral-400";
                            if (it.evaluation_status === "CORRECT") {
                                dotStyle = "bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100";
                            } else if (it.evaluation_status === "INCORRECT") {
                                dotStyle = "bg-red-50 text-red-800 border-red-300 hover:bg-red-100";
                            } else if (it.evaluation_status === "PENDING_EVALUATION") {
                                dotStyle = "bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100";
                            }

                            return (
                                <button
                                    key={it.id}
                                    type="button"
                                    onClick={() => scrollToQuestion(it.question_number)}
                                    title={`Q${it.question_number} (${it.evaluation_status})`}
                                    className={`w-7 h-7 rounded-md border text-xs font-semibold flex items-center justify-center transition-colors cursor-pointer ${dotStyle}`}
                                >
                                    {it.question_number}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </Card>

            {/* Questions List */}
            {filteredItems.length > 0 ? (
                <div className="space-y-5">
                    {filteredItems.map((item) => (
                        <QuestionReviewItem
                            key={item.id}
                            item={item}
                            isFinalized={isFinalized}
                        />
                    ))}
                </div>
            ) : (
                <Card className="p-8 text-center border-border bg-surface space-y-2">
                    <span className="text-sm font-semibold text-foreground block">
                        No questions in this filter
                    </span>
                    <p className="text-xs text-foreground-muted">
                        No questions match the current filter selection ({activeFilter}).
                    </p>
                    <div className="pt-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                                setActiveFilter("ALL");
                                setSelectedSection("ALL");
                            }}
                        >
                            Reset Filter
                        </Button>
                    </div>
                </Card>
            )}
        </div>
    );
};
