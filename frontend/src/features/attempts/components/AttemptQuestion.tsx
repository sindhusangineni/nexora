import React, { useState } from "react";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { McqResponse } from "./ResponseControls/McqResponse";
import { MultipleSelectResponse } from "./ResponseControls/MultipleSelectResponse";
import { TrueFalseResponse } from "./ResponseControls/TrueFalseResponse";
import { AssertionReasonResponse } from "./ResponseControls/AssertionReasonResponse";
import { MatchFollowingResponse } from "./ResponseControls/MatchFollowingResponse";
import { DescriptiveResponse } from "./ResponseControls/DescriptiveResponse";
import { ResponseSaveIndicator, type SaveStatus } from "./ResponseSaveIndicator";
import type {
    AttemptItemDelivery,
    DeliveryQuestionVersion,
    SaveResponsePayload,
    SelectedMatch,
} from "../types/attempt.types";

interface AttemptQuestionProps {
    item: AttemptItemDelivery;
    questionVersion?: DeliveryQuestionVersion;
    index: number;
    totalCount: number;
    sectionTitle?: string;
    saveStatus: SaveStatus;
    saveErrorMessage?: string;
    onSave: (payload: SaveResponsePayload) => void;
    onClear: () => void;
    onPrevious?: () => void;
    onNext?: () => void;
    hasPrevious: boolean;
    hasNext: boolean;
    disabled?: boolean;
}

export const AttemptQuestion: React.FC<AttemptQuestionProps> = ({
    item,
    questionVersion,
    index,
    totalCount,
    sectionTitle,
    saveStatus,
    saveErrorMessage,
    onSave,
    onClear,
    onPrevious,
    onNext,
    hasPrevious,
    hasNext,
    disabled = false,
}) => {
    const qType = questionVersion?.question_type || "MCQ";
    const resp = item.response;

    // Local answer state initialized from current server response
    const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(
        resp?.selected_choice_ids?.[0] || null,
    );
    const [selectedChoiceIds, setSelectedChoiceIds] = useState<string[]>(
        resp?.selected_choice_ids || [],
    );
    const [booleanResponse, setBooleanResponse] = useState<boolean | null>(
        resp?.boolean_response ?? null,
    );
    const [assertionReasonResponse, setAssertionReasonResponse] = useState<string | null>(
        resp?.assertion_reason_response || null,
    );
    const [matchPairs, setMatchPairs] = useState<SelectedMatch[]>(
        resp?.selected_matches || [],
    );
    const [textResponse, setTextResponse] = useState<string>(
        resp?.text_response || "",
    );

    // Handle immediate or explicit save
    const handleSaveCurrent = () => {
        let payload: SaveResponsePayload = { question_type: qType };

        if (qType === "MCQ") {
            if (!selectedChoiceId) return;
            payload = { ...payload, choice_id: selectedChoiceId };
        } else if (qType === "MULTIPLE_SELECT") {
            if (selectedChoiceIds.length === 0) return;
            payload = { ...payload, selected_choice_ids: selectedChoiceIds };
        } else if (qType === "TRUE_FALSE") {
            if (booleanResponse === null) return;
            payload = { ...payload, boolean_response: booleanResponse };
        } else if (qType === "ASSERTION_REASON") {
            if (!assertionReasonResponse) return;
            payload = { ...payload, assertion_reason_response: assertionReasonResponse };
        } else if (qType === "MATCH_FOLLOWING") {
            if (matchPairs.length === 0) return;
            payload = { ...payload, match_pairs: matchPairs };
        } else if (qType === "DESCRIPTIVE") {
            if (!textResponse.trim()) return;
            payload = { ...payload, text_response: textResponse.trim() };
        }

        onSave(payload);
    };

    // Auto-save choice selection for direct-click items
    const handleMcqSelect = (choiceId: string) => {
        setSelectedChoiceId(choiceId);
        onSave({ question_type: "MCQ", choice_id: choiceId });
    };

    const handleMultipleSelectToggle = (choiceIds: string[]) => {
        setSelectedChoiceIds(choiceIds);
        onSave({ question_type: "MULTIPLE_SELECT", selected_choice_ids: choiceIds });
    };

    const handleTrueFalseSelect = (val: boolean) => {
        setBooleanResponse(val);
        onSave({ question_type: "TRUE_FALSE", boolean_response: val });
    };

    const handleAssertionReasonSelect = (val: string) => {
        setAssertionReasonResponse(val);
        onSave({ question_type: "ASSERTION_REASON", assertion_reason_response: val });
    };

    const handleMatchesChange = (matches: SelectedMatch[]) => {
        setMatchPairs(matches);
        onSave({ question_type: "MATCH_FOLLOWING", match_pairs: matches });
    };

    const isAnswered = resp?.answer_state === "ANSWERED";

    return (
        <article className="space-y-6">
            {/* Header info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-3">
                <div className="flex items-center space-x-3 flex-wrap gap-y-1">
                    <span className="text-sm font-bold text-neutral-900 tracking-tight">
                        Question {index + 1} of {totalCount}
                    </span>
                    {sectionTitle && (
                        <Badge variant="default" size="sm">
                            {sectionTitle}
                        </Badge>
                    )}
                    <Badge variant="info" size="sm">
                        {qType}
                    </Badge>
                </div>

                <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-sm border border-emerald-200">
                        +{item.allocated_marks}
                    </span>
                    {parseFloat(item.allocated_penalty) > 0 && (
                        <span className="text-xs font-semibold text-red-700 bg-red-50 px-2 py-0.5 rounded-sm border border-red-200">
                            -{item.allocated_penalty}
                        </span>
                    )}
                    <ResponseSaveIndicator
                        status={saveStatus}
                        errorMessage={saveErrorMessage}
                        onRetry={handleSaveCurrent}
                        className="ml-2"
                    />
                </div>
            </div>

            {/* Question Text */}
            <div className="text-base text-neutral-900 leading-relaxed font-normal whitespace-pre-line">
                {questionVersion?.text || `Loading question ${index + 1}...`}
            </div>

            {/* Answer Control Body */}
            <div className="pt-2">
                {qType === "MCQ" && (
                    <McqResponse
                        choices={questionVersion?.content?.choices || []}
                        selectedChoiceId={selectedChoiceId}
                        onChange={handleMcqSelect}
                        disabled={disabled}
                    />
                )}

                {qType === "MULTIPLE_SELECT" && (
                    <MultipleSelectResponse
                        choices={questionVersion?.content?.choices || []}
                        selectedChoiceIds={selectedChoiceIds}
                        onChange={handleMultipleSelectToggle}
                        disabled={disabled}
                    />
                )}

                {qType === "TRUE_FALSE" && (
                    <TrueFalseResponse
                        value={booleanResponse}
                        onChange={handleTrueFalseSelect}
                        disabled={disabled}
                    />
                )}

                {qType === "ASSERTION_REASON" && (
                    <AssertionReasonResponse
                        assertion={questionVersion?.content?.assertion}
                        reason={questionVersion?.content?.reason}
                        value={assertionReasonResponse}
                        onChange={handleAssertionReasonSelect}
                        disabled={disabled}
                    />
                )}

                {qType === "MATCH_FOLLOWING" && (
                    <MatchFollowingResponse
                        leftItems={questionVersion?.content?.left_items || []}
                        rightItems={questionVersion?.content?.right_items || []}
                        selectedMatches={matchPairs}
                        onChange={handleMatchesChange}
                        disabled={disabled}
                    />
                )}

                {qType === "DESCRIPTIVE" && (
                    <div className="space-y-3">
                        <DescriptiveResponse
                            value={textResponse}
                            onChange={setTextResponse}
                            disabled={disabled}
                        />
                        <div className="flex justify-end">
                            <Button
                                size="sm"
                                variant="secondary"
                                onClick={handleSaveCurrent}
                                disabled={disabled || !textResponse.trim()}
                            >
                                Save Written Answer
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            {/* Question Action Footer */}
            <div className="pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                    {isAnswered && !disabled && (
                        <button
                            type="button"
                            onClick={onClear}
                            className="text-xs text-neutral-500 hover:text-red-600 font-medium transition-colors cursor-pointer"
                        >
                            Clear Answer
                        </button>
                    )}
                </div>

                <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
                    <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={onPrevious}
                        disabled={!hasPrevious || disabled}
                        className="flex-1 sm:flex-none"
                    >
                        Previous
                    </Button>

                    <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={onNext}
                        disabled={!hasNext || disabled}
                        className="flex-1 sm:flex-none"
                    >
                        Next
                    </Button>
                </div>
            </div>
        </article>
    );
};
