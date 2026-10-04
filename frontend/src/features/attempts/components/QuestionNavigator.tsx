import React from "react";
import type { AttemptItemDelivery } from "../types/attempt.types";
import type { AssessmentSection } from "@/features/assessment/types/assessment.types";

interface QuestionNavigatorProps {
    items: AttemptItemDelivery[];
    currentIndex: number;
    onSelectIndex: (index: number) => void;
    sections?: AssessmentSection[];
    className?: string;
}

export const QuestionNavigator: React.FC<QuestionNavigatorProps> = ({
    items,
    currentIndex,
    onSelectIndex,
    sections = [],
    className = "",
}) => {
    // If sections are provided, group items by section
    const sectionMap = new Map<string, AssessmentSection>();
    sections.forEach((s) => sectionMap.set(s.id, s));

    const hasSections = sections.length > 0;

    // Group items by section id (or "default")
    const groups: { title: string; itemsWithIndex: { item: AttemptItemDelivery; index: number }[] }[] = [];

    if (hasSections) {
        sections.forEach((sec) => {
            const sectionItems: { item: AttemptItemDelivery; index: number }[] = [];
            items.forEach((item, idx) => {
                if (item.assessment_section_id === sec.id) {
                    sectionItems.push({ item, index: idx });
                }
            });
            if (sectionItems.length > 0) {
                groups.push({
                    title: sec.title,
                    itemsWithIndex: sectionItems,
                });
            }
        });

        // Any items without section
        const unassigned: { item: AttemptItemDelivery; index: number }[] = [];
        items.forEach((item, idx) => {
            if (!item.assessment_section_id || !sectionMap.has(item.assessment_section_id)) {
                unassigned.push({ item, index: idx });
            }
        });
        if (unassigned.length > 0) {
            groups.push({
                title: "General",
                itemsWithIndex: unassigned,
            });
        }
    } else {
        groups.push({
            title: "Questions",
            itemsWithIndex: items.map((item, idx) => ({ item, index: idx })),
        });
    }

    return (
        <nav aria-label="Question Navigator" className={`space-y-4 ${className}`}>
            {groups.map((group, gIdx) => (
                <div key={gIdx} className="space-y-2">
                    {hasSections && (
                        <h4 className="text-xs font-semibold text-foreground tracking-tight border-b border-border/60 pb-1">
                            {group.title}
                        </h4>
                    )}
                    <div className="grid grid-cols-5 gap-2">
                        {group.itemsWithIndex.map(({ item, index }) => {
                            const isCurrent = currentIndex === index;
                            const isAnswered = item.response?.answer_state === "ANSWERED";

                            return (
                                <button
                                    key={item.id}
                                    type="button"
                                    onClick={() => onSelectIndex(index)}
                                    className={`relative flex items-center justify-center h-10 sm:h-9 min-w-[36px] rounded-md text-xs font-semibold transition-all cursor-pointer ${
                                        isCurrent
                                            ? "ring-2 ring-primary ring-offset-1 z-10"
                                            : ""
                                    } ${
                                        isAnswered
                                            ? "bg-neutral-900 text-white hover:bg-neutral-800"
                                            : "bg-surface border border-border text-neutral-700 hover:border-neutral-300 hover:bg-neutral-50"
                                    }`}
                                    aria-current={isCurrent ? "true" : undefined}
                                    aria-label={`Question ${index + 1}, ${
                                        isAnswered ? "Answered" : "Unanswered"
                                    }`}
                                >
                                    {index + 1}
                                </button>
                            );
                        })}
                    </div>
                </div>
            ))}

            {/* Legend */}
            <div className="pt-3 border-t border-border flex items-center justify-between text-[11px] text-foreground-muted">
                <div className="flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-xs bg-neutral-900" />
                    <span>Answered</span>
                </div>
                <div className="flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-xs bg-surface border border-border" />
                    <span>Unanswered</span>
                </div>
                <div className="flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-xs ring-2 ring-primary bg-surface" />
                    <span>Current</span>
                </div>
            </div>
        </nav>
    );
};
