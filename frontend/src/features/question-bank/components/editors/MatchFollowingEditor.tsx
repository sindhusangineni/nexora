import { Button } from "@/shared/ui/Button";
import type { MatchItem, MatchPair } from "../../types/questionBank.types";

export interface MatchFollowingEditorProps {
    leftItems: MatchItem[];
    rightItems: MatchItem[];
    pairs: MatchPair[];
    onChange: (data: {
        leftItems: MatchItem[];
        rightItems: MatchItem[];
        pairs: MatchPair[];
    }) => void;
    disabled?: boolean;
    error?: string;
}

export function MatchFollowingEditor({
    leftItems,
    rightItems,
    pairs,
    onChange,
    disabled = false,
    error,
}: MatchFollowingEditorProps) {
    const handleLeftTextChange = (index: number, text: string) => {
        const nextLeft = leftItems.map((item, i) =>
            i === index ? { ...item, text, position: i + 1 } : { ...item, position: i + 1 },
        );
        onChange({ leftItems: nextLeft, rightItems, pairs });
    };

    const handleRightTextChange = (index: number, text: string) => {
        const nextRight = rightItems.map((item, i) =>
            i === index ? { ...item, text, position: i + 1 } : { ...item, position: i + 1 },
        );
        onChange({ leftItems, rightItems: nextRight, pairs });
    };

    const handleAddLeftItem = () => {
        const nextPos = leftItems.length + 1;
        const nextLeft = [...leftItems, { text: "", position: nextPos }];
        // Add a default pair for this new item to the first right item if available
        const nextPairs = [
            ...pairs,
            { left_position: nextPos, right_position: 1 },
        ];
        onChange({ leftItems: nextLeft, rightItems, pairs: nextPairs });
    };

    const handleAddRightItem = () => {
        const nextPos = rightItems.length + 1;
        const nextRight = [...rightItems, { text: "", position: nextPos }];
        onChange({ leftItems, rightItems: nextRight, pairs });
    };

    const handleRemoveLeftItem = (index: number) => {
        if (leftItems.length <= 2) return;
        const removedPos = leftItems[index].position;
        const nextLeft = leftItems
            .filter((_, i) => i !== index)
            .map((item, i) => ({ ...item, position: i + 1 }));
        const nextPairs = pairs
            .filter((p) => p.left_position !== removedPos)
            .map((p) => ({
                left_position:
                    p.left_position > removedPos
                        ? p.left_position - 1
                        : p.left_position,
                right_position: p.right_position,
            }));
        onChange({ leftItems: nextLeft, rightItems, pairs: nextPairs });
    };

    const handleRemoveRightItem = (index: number) => {
        if (rightItems.length <= 2) return;
        const removedPos = rightItems[index].position;
        const nextRight = rightItems
            .filter((_, i) => i !== index)
            .map((item, i) => ({ ...item, position: i + 1 }));
        const nextPairs = pairs.map((p) => ({
            left_position: p.left_position,
            right_position:
                p.right_position === removedPos
                    ? 1
                    : p.right_position > removedPos
                    ? p.right_position - 1
                    : p.right_position,
        }));
        onChange({ leftItems, rightItems: nextRight, pairs: nextPairs });
    };

    const handlePairChange = (leftPos: number, rightPos: number) => {
        const existingIdx = pairs.findIndex((p) => p.left_position === leftPos);
        let nextPairs: MatchPair[];
        if (existingIdx >= 0) {
            nextPairs = pairs.map((p) =>
                p.left_position === leftPos
                    ? { left_position: leftPos, right_position: rightPos }
                    : p,
            );
        } else {
            nextPairs = [...pairs, { left_position: leftPos, right_position: rightPos }];
        }
        onChange({ leftItems, rightItems, pairs: nextPairs });
    };

    const rightLabels = ["A", "B", "C", "D", "E", "F", "G", "H"];

    return (
        <div className="space-y-6">
            <div>
                <h4 className="text-sm font-semibold text-foreground tracking-tight">
                    Match the Following Columns & Pairs
                </h4>
                <p className="text-xs text-foreground-muted">
                    Configure items in Column I and Column II, then establish the correct pairwise matches.
                </p>
            </div>

            {error && (
                <p className="text-xs font-medium text-danger" role="alert">
                    {error}
                </p>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Column I (Left) */}
                <div className="space-y-3 p-4 rounded-xl border border-border bg-surface-muted/30">
                    <div className="flex items-center justify-between pb-2 border-b border-border">
                        <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                            Column I (Left Items)
                        </span>
                        <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            onClick={handleAddLeftItem}
                            disabled={disabled || leftItems.length >= 8}
                        >
                            + Add Left
                        </Button>
                    </div>

                    <div className="space-y-2">
                        {leftItems.map((item, index) => (
                            <div key={index} className="flex items-center gap-2">
                                <span className="w-6 h-6 rounded bg-neutral-200 text-neutral-800 text-xs font-bold flex items-center justify-center shrink-0">
                                    {index + 1}
                                </span>
                                <input
                                    type="text"
                                    value={item.text}
                                    onChange={(e) => handleLeftTextChange(index, e.target.value)}
                                    disabled={disabled}
                                    placeholder={`Left item ${index + 1}...`}
                                    aria-label={`Column I item ${index + 1}`}
                                    className="flex-1 h-9 px-3 text-xs rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-1 focus:ring-primary-500"
                                />
                                {leftItems.length > 2 && (
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveLeftItem(index)}
                                        disabled={disabled}
                                        aria-label={`Remove left item ${index + 1}`}
                                        className="text-foreground-muted hover:text-danger p-1"
                                    >
                                        ✕
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Column II (Right) */}
                <div className="space-y-3 p-4 rounded-xl border border-border bg-surface-muted/30">
                    <div className="flex items-center justify-between pb-2 border-b border-border">
                        <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                            Column II (Right Items)
                        </span>
                        <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            onClick={handleAddRightItem}
                            disabled={disabled || rightItems.length >= 8}
                        >
                            + Add Right
                        </Button>
                    </div>

                    <div className="space-y-2">
                        {rightItems.map((item, index) => {
                            const label = rightLabels[index] || `${index + 1}`;
                            return (
                                <div key={index} className="flex items-center gap-2">
                                    <span className="w-6 h-6 rounded bg-neutral-200 text-neutral-800 text-xs font-bold flex items-center justify-center shrink-0">
                                        {label}
                                    </span>
                                    <input
                                        type="text"
                                        value={item.text}
                                        onChange={(e) =>
                                            handleRightTextChange(index, e.target.value)
                                        }
                                        disabled={disabled}
                                        placeholder={`Right item ${label}...`}
                                        aria-label={`Column II item ${label}`}
                                        className="flex-1 h-9 px-3 text-xs rounded-md border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-1 focus:ring-primary-500"
                                    />
                                    {rightItems.length > 2 && (
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveRightItem(index)}
                                            disabled={disabled}
                                            aria-label={`Remove right item ${label}`}
                                            className="text-foreground-muted hover:text-danger p-1"
                                        >
                                            ✕
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Matching Pairs Table */}
            <div className="p-4 rounded-xl border border-border bg-surface space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-foreground block">
                    Correct Pair Mappings
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {leftItems.map((leftItem, index) => {
                        const leftPos = leftItem.position || index + 1;
                        const currentPair = pairs.find((p) => p.left_position === leftPos);
                        const selectedRightPos = currentPair ? currentPair.right_position : 1;

                        return (
                            <div
                                key={leftPos}
                                className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-surface-muted/50 text-xs"
                            >
                                <span className="font-semibold text-neutral-900">
                                    Item {leftPos} →
                                </span>
                                <select
                                    value={selectedRightPos}
                                    onChange={(e) =>
                                        handlePairChange(leftPos, parseInt(e.target.value, 10))
                                    }
                                    disabled={disabled}
                                    aria-label={`Match for item ${leftPos}`}
                                    className="h-8 px-2 rounded border border-border bg-surface text-foreground font-semibold"
                                >
                                    {rightItems.map((_, rIdx) => {
                                        const rPos = rIdx + 1;
                                        const rLabel = rightLabels[rIdx] || `${rPos}`;
                                        return (
                                            <option key={rPos} value={rPos}>
                                                Item {rLabel}
                                            </option>
                                        );
                                    })}
                                </select>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
