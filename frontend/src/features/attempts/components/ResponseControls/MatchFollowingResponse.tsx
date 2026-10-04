import React from "react";
import type { DeliveryMatchItem, SelectedMatch } from "../../types/attempt.types";

interface MatchFollowingResponseProps {
    leftItems: DeliveryMatchItem[];
    rightItems: DeliveryMatchItem[];
    selectedMatches: SelectedMatch[];
    onChange: (matches: SelectedMatch[]) => void;
    disabled?: boolean;
}

export const MatchFollowingResponse: React.FC<MatchFollowingResponseProps> = ({
    leftItems,
    rightItems,
    selectedMatches,
    onChange,
    disabled = false,
}) => {
    // Map current left items to their selected right item id
    const matchMap = new Map<string, string>();
    selectedMatches.forEach((m) => {
        matchMap.set(m.left_item_id, m.right_item_id);
    });

    const handleSelect = (leftId: string, rightId: string) => {
        if (disabled) return;

        const nextMatches: SelectedMatch[] = [];
        leftItems.forEach((item) => {
            const currentRight = item.id === leftId ? rightId : matchMap.get(item.id);
            if (currentRight) {
                nextMatches.push({
                    left_item_id: item.id,
                    right_item_id: currentRight,
                });
            }
        });

        onChange(nextMatches);
    };

    // Check for duplicates
    const selectedRightIds = Array.from(matchMap.values());
    const hasDuplicateRight = new Set(selectedRightIds).size !== selectedRightIds.length;

    return (
        <div className="space-y-4">
            <div className="text-xs text-foreground-muted">
                Match each item in Column I with the corresponding item in Column II. Each option in Column II may only be mapped once.
            </div>

            <div className="space-y-3">
                {leftItems.map((left, idx) => {
                    const currentRightId = matchMap.get(left.id) || "";

                    return (
                        <div
                            key={left.id}
                            className="p-3.5 bg-surface border border-border rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm shadow-2xs"
                        >
                            <div className="flex items-start space-x-2.5 sm:w-1/2">
                                <span className="flex items-center justify-center w-5 h-5 rounded-sm bg-neutral-100 text-neutral-700 text-xs font-semibold shrink-0 mt-0.5">
                                    {idx + 1}
                                </span>
                                <span className="font-medium text-neutral-900 leading-snug">
                                    {left.text}
                                </span>
                            </div>

                            <div className="sm:w-1/2">
                                <label htmlFor={`match-select-${left.id}`} className="sr-only">
                                    Match for {left.text}
                                </label>
                                <select
                                    id={`match-select-${left.id}`}
                                    value={currentRightId}
                                    onChange={(e) => handleSelect(left.id, e.target.value)}
                                    disabled={disabled}
                                    className="w-full min-h-[44px] px-3 py-2.5 sm:py-2 bg-white border border-border rounded-md text-xs sm:text-sm font-medium text-neutral-800 focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
                                >
                                    <option value="">-- Select matching option --</option>
                                    {rightItems.map((right, rIdx) => {
                                        const rLetter = String.fromCharCode(65 + rIdx);
                                        return (
                                            <option key={right.id} value={right.id}>
                                                ({rLetter}) {right.text}
                                            </option>
                                        );
                                    })}
                                </select>
                            </div>
                        </div>
                    );
                })}
            </div>

            {hasDuplicateRight && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-800">
                    <strong>Warning:</strong> You have selected the same option in Column II for multiple items. Each match must be distinct (injective).
                </div>
            )}
        </div>
    );
};
