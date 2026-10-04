import React, { useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import {
    CheckCircleIcon,
    XCircleIcon,
    MinusCircleIcon,
    ClockIcon,
    LightbulbIcon,
    ChevronDownIcon,
    ChevronUpIcon,
    LockIcon,
} from "./Icons";
import type { StudentQuestionReviewItem } from "../types/attempt.types";

interface QuestionReviewItemProps {
    item: StudentQuestionReviewItem;
    isFinalized: boolean;
}

export const QuestionReviewItem: React.FC<QuestionReviewItemProps> = ({
    item,
    isFinalized,
}) => {
    const [isExplanationOpen, setIsExplanationOpen] = useState(true);

    const isPending = item.evaluation_status === "PENDING_EVALUATION";
    const isCorrect = item.evaluation_status === "CORRECT";
    const isIncorrect = item.evaluation_status === "INCORRECT";
    const isPartiallyCorrect = item.evaluation_status === "PARTIALLY_CORRECT";

    const renderEvaluationBadge = () => {
        if (isPending) {
            return (
                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                    <ClockIcon className="w-3.5 h-3.5 animate-pulse" />
                    <span>Evaluation Pending</span>
                </span>
            );
        }
        if (isCorrect) {
            return (
                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                    <CheckCircleIcon className="w-3.5 h-3.5" />
                    <span>Correct</span>
                </span>
            );
        }
        if (isPartiallyCorrect) {
            return (
                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                    <CheckCircleIcon className="w-3.5 h-3.5" />
                    <span>Partially Correct</span>
                </span>
            );
        }
        if (isIncorrect) {
            return (
                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-800 border border-red-200">
                    <XCircleIcon className="w-3.5 h-3.5" />
                    <span>Incorrect</span>
                </span>
            );
        }
        return (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-neutral-100 text-neutral-700 border border-neutral-200">
                <MinusCircleIcon className="w-3.5 h-3.5" />
                <span>Unanswered</span>
            </span>
        );
    };

    const renderMarksBadge = () => {
        if (isPending) {
            return (
                <span className="text-xs font-medium text-foreground-muted">
                    Marks: <span className="font-semibold text-amber-700">Pending</span> / {item.allocated_marks}
                </span>
            );
        }

        const awarded = item.marks_awarded !== null ? parseFloat(item.marks_awarded) : 0;
        const allocated = parseFloat(item.allocated_marks);

        return (
            <span className="text-xs font-medium text-foreground-muted">
                Marks:{" "}
                <span
                    className={`font-bold ${
                        awarded > 0
                            ? "text-emerald-700"
                            : awarded < 0
                            ? "text-red-700"
                            : "text-foreground"
                    }`}
                >
                    {item.marks_awarded ?? "0.00"}
                </span>{" "}
                / {allocated.toFixed(2)}
                {parseFloat(item.allocated_penalty) > 0 && (
                    <span className="text-foreground-muted/70 text-[11px] ml-1">
                        (-{item.allocated_penalty} penalty)
                    </span>
                )}
            </span>
        );
    };

    const formatQuestionType = (type: string) => {
        switch (type) {
            case "MCQ":
                return "Single Choice (MCQ)";
            case "MULTIPLE_SELECT":
                return "Multiple Select";
            case "TRUE_FALSE":
                return "True / False";
            case "ASSERTION_REASON":
                return "Assertion & Reason";
            case "MATCH_FOLLOWING":
                return "Match the Following";
            case "DESCRIPTIVE":
                return "Descriptive / Long Answer";
            default:
                return type;
        }
    };

    const formatArRelationship = (rel?: string | null) => {
        if (!rel) return "None Selected";
        switch (rel) {
            case "BOTH_TRUE_REASON_CORRECT":
                return "Both (A) and (R) are true, and (R) is the correct explanation of (A)";
            case "BOTH_TRUE_REASON_NOT_CORRECT":
                return "Both (A) and (R) are true, but (R) is NOT the correct explanation of (A)";
            case "ASSERTION_TRUE_REASON_FALSE":
                return "(A) is true, but (R) is false";
            case "ASSERTION_FALSE_REASON_FALSE":
                return "Both (A) and (R) are false";
            default:
                return rel;
        }
    };

    // Render type-specific body
    const renderTypeContent = () => {
        const qType = item.question_type;

        // 1. MCQ & MULTIPLE_SELECT
        if (qType === "MCQ" || qType === "MULTIPLE_SELECT") {
            const choices = item.choices || [];
            const selectedChoiceId = item.candidate_answer?.selected_choice_id;
            const selectedChoiceIds: string[] =
                item.candidate_answer?.selected_choice_ids || (selectedChoiceId ? [selectedChoiceId] : []);

            const correctChoiceId = item.correct_answer?.correct_choice_id;
            const correctChoiceIds: string[] =
                item.correct_answer?.correct_choice_ids || (correctChoiceId ? [correctChoiceId] : []);

            return (
                <div className="space-y-2.5">
                    {choices.map((choice, idx) => {
                        const isSelected = selectedChoiceIds.includes(choice.id);
                        const isCorrectChoice = isFinalized && correctChoiceIds.includes(choice.id);

                        let borderClass = "border-border bg-surface";
                        let indicatorBadge = null;

                        if (isFinalized) {
                            if (isCorrectChoice && isSelected) {
                                borderClass = "border-emerald-500 bg-emerald-50/60 text-emerald-950 font-medium";
                                indicatorBadge = (
                                    <span className="inline-flex items-center space-x-1 text-[11px] font-bold text-emerald-800 bg-emerald-100/90 px-2 py-0.5 rounded-md">
                                        <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-700" />
                                        <span>Your Answer (Correct)</span>
                                    </span>
                                );
                            } else if (isCorrectChoice && !isSelected) {
                                borderClass = "border-emerald-300 bg-emerald-50/30 text-emerald-900";
                                indicatorBadge = (
                                    <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-emerald-800 bg-emerald-100/60 px-2 py-0.5 rounded-md">
                                        <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-600" />
                                        <span>Correct Answer</span>
                                    </span>
                                );
                            } else if (isSelected && !isCorrectChoice) {
                                borderClass = "border-red-400 bg-red-50/50 text-red-950";
                                indicatorBadge = (
                                    <span className="inline-flex items-center space-x-1 text-[11px] font-bold text-red-800 bg-red-100 px-2 py-0.5 rounded-md">
                                        <XCircleIcon className="w-3.5 h-3.5 text-red-600" />
                                        <span>Your Answer (Incorrect)</span>
                                    </span>
                                );
                            }
                        } else if (isSelected) {
                            borderClass = "border-primary-400 bg-primary-50/50 text-primary-950 font-medium";
                            indicatorBadge = (
                                <span className="text-[11px] font-semibold text-primary-800 bg-primary-100 px-2 py-0.5 rounded-md">
                                    Your Answer
                                </span>
                            );
                        }

                        return (
                            <div
                                key={choice.id}
                                className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 text-xs sm:text-sm transition-colors ${borderClass}`}
                            >
                                <div className="flex items-center space-x-3">
                                    <span className="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs bg-neutral-100 border border-neutral-200 text-neutral-700 shrink-0">
                                        {String.fromCharCode(65 + idx)}
                                    </span>
                                    <span className="leading-relaxed">{choice.text}</span>
                                </div>
                                {indicatorBadge}
                            </div>
                        );
                    })}
                </div>
            );
        }

        // 2. TRUE_FALSE
        if (qType === "TRUE_FALSE") {
            const candidateBool = item.candidate_answer?.boolean_response;
            const correctBool = isFinalized ? item.correct_answer?.correct_boolean : null;

            return (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                    {[true, false].map((val) => {
                        const isSelected = candidateBool === val;
                        const isCorrectVal = isFinalized && correctBool === val;

                        let cardStyle = "border-border bg-surface text-foreground";
                        let statusText = null;

                        if (isFinalized) {
                            if (isCorrectVal && isSelected) {
                                cardStyle = "border-emerald-500 bg-emerald-50/60 text-emerald-950 font-medium";
                                statusText = "Your Answer (Correct)";
                            } else if (isCorrectVal && !isSelected) {
                                cardStyle = "border-emerald-300 bg-emerald-50/30 text-emerald-900";
                                statusText = "Correct Answer";
                            } else if (isSelected && !isCorrectVal) {
                                cardStyle = "border-red-400 bg-red-50/50 text-red-950";
                                statusText = "Your Answer (Incorrect)";
                            }
                        } else if (isSelected) {
                            cardStyle = "border-primary-400 bg-primary-50/50 text-primary-950 font-medium";
                            statusText = "Your Answer";
                        }

                        return (
                            <div
                                key={String(val)}
                                className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center space-y-1.5 transition-colors ${cardStyle}`}
                            >
                                <span className="text-base font-bold uppercase tracking-wider">
                                    {val ? "True" : "False"}
                                </span>
                                {statusText && (
                                    <span className="text-[11px] font-semibold">
                                        {statusText}
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
            );
        }

        // 3. ASSERTION_REASON
        if (qType === "ASSERTION_REASON") {
            const candRel = item.candidate_answer?.assertion_reason_response;
            const corrRel = isFinalized ? item.correct_answer?.correct_relationship : null;

            return (
                <div className="space-y-4">
                    {/* Statements box */}
                    <div className="p-4 rounded-xl bg-surface-muted/40 border border-border space-y-3">
                        <div className="flex items-start space-x-2">
                            <span className="font-bold text-xs px-2 py-0.5 rounded bg-primary-100 text-primary-800 shrink-0">
                                Assertion (A)
                            </span>
                            <p className="text-xs sm:text-sm text-foreground leading-relaxed">
                                {item.assertion || "Assertion statement"}
                            </p>
                        </div>
                        <div className="flex items-start space-x-2">
                            <span className="font-bold text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 shrink-0">
                                Reason (R)
                            </span>
                            <p className="text-xs sm:text-sm text-foreground leading-relaxed">
                                {item.reason || "Reason statement"}
                            </p>
                        </div>
                    </div>

                    {/* Relationship Selection & Comparison */}
                    <div className="space-y-2">
                        <div className="p-3.5 rounded-xl border border-border bg-surface text-xs space-y-1">
                            <span className="text-foreground-muted font-medium block">
                                Your Selection:
                            </span>
                            <p className="font-semibold text-foreground">
                                {formatArRelationship(candRel)}
                            </p>
                        </div>

                        {isFinalized && corrRel && (
                            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/40 text-xs space-y-1">
                                <span className="text-emerald-800 font-bold block flex items-center space-x-1">
                                    <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-700" />
                                    <span>Correct Relationship:</span>
                                </span>
                                <p className="font-semibold text-emerald-950">
                                    {formatArRelationship(corrRel)}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        // 4. MATCH_FOLLOWING
        if (qType === "MATCH_FOLLOWING") {
            const leftItems = item.left_items || [];
            const rightItems = item.right_items || [];
            const candMatches: Array<{ left_item_id: string; right_item_id: string }> =
                item.candidate_answer?.matches || [];
            const corrMatches: Array<{ left_item_id: string; right_item_id: string }> =
                isFinalized ? item.correct_answer?.correct_matches || [] : [];

            const rightTextMap = new Map(rightItems.map((r) => [r.id, r.text]));
            const candMatchMap = new Map(candMatches.map((m) => [m.left_item_id, m.right_item_id]));
            const corrMatchMap = new Map(corrMatches.map((m) => [m.left_item_id, m.right_item_id]));

            return (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {leftItems.map((left, idx) => {
                            const userRightId = candMatchMap.get(left.id);
                            const userRightText = userRightId ? rightTextMap.get(userRightId) || "Selected Item" : "None";

                            const corrRightId = corrMatchMap.get(left.id);
                            const corrRightText = corrRightId ? rightTextMap.get(corrRightId) || "Correct Item" : "";

                            const isPairCorrect = isFinalized && userRightId === corrRightId;

                            return (
                                <div
                                    key={left.id}
                                    className={`p-3.5 rounded-xl border text-xs space-y-2 ${
                                        isFinalized
                                            ? isPairCorrect
                                                ? "border-emerald-300 bg-emerald-50/30"
                                                : "border-red-200 bg-red-50/20"
                                            : "border-border bg-surface"
                                    }`}
                                >
                                    <div className="font-semibold text-foreground">
                                        {idx + 1}. {left.text}
                                    </div>
                                    <div className="space-y-1">
                                        <div className="text-foreground-muted flex items-center justify-between">
                                            <span>Your Match:</span>
                                            <span className="font-medium text-foreground">
                                                {userRightText}
                                            </span>
                                        </div>
                                        {isFinalized && corrRightText && !isPairCorrect && (
                                            <div className="text-emerald-800 font-semibold flex items-center justify-between pt-1 border-t border-border/50">
                                                <span>Correct Match:</span>
                                                <span>{corrRightText}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            );
        }

        // 5. DESCRIPTIVE
        if (qType === "DESCRIPTIVE") {
            const userResponse = item.candidate_answer?.text_response;
            const modelAnswer = isFinalized ? item.correct_answer?.model_answer : null;

            return (
                <div className="space-y-4">
                    {/* Student response */}
                    <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-foreground-muted uppercase tracking-wider block">
                            Your Submitted Response
                        </span>
                        <div className="p-4 rounded-xl border border-border bg-surface text-xs sm:text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                            {userResponse ? userResponse : <span className="text-foreground-muted italic">No response submitted.</span>}
                        </div>
                    </div>

                    {/* Pending Evaluation notice or graded feedback */}
                    {isPending ? (
                        <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 flex items-start space-x-3 text-xs">
                            <ClockIcon className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                            <div>
                                <span className="font-bold text-amber-900 block">
                                    Descriptive Evaluation Pending
                                </span>
                                <p className="text-amber-800 mt-0.5 leading-relaxed">
                                    Your response has been submitted and is currently being evaluated by an instructor. Model answer and awarded marks will appear once finalized.
                                </p>
                            </div>
                        </div>
                    ) : (
                        modelAnswer && (
                            <div className="space-y-1.5">
                                <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider block flex items-center space-x-1">
                                    <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-600" />
                                    <span>Model Answer / Key Points</span>
                                </span>
                                <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 text-xs sm:text-sm text-emerald-950 whitespace-pre-wrap leading-relaxed">
                                    {modelAnswer}
                                </div>
                            </div>
                        )
                    )}
                </div>
            );
        }

        return null;
    };

    return (
        <Card
            id={`question-review-${item.question_number}`}
            className="p-5 sm:p-6 space-y-5 border-border bg-surface shadow-xs transition-shadow hover:shadow-sm"
        >
            {/* Header: Question Number, Section, Type, Status & Marks */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-bold text-foreground">
                        Q{item.question_number}
                    </span>
                    <Badge variant="primary" size="sm">
                        {formatQuestionType(item.question_type)}
                    </Badge>
                    {item.section_name && (
                        <Badge variant="outline" size="sm">
                            {item.section_name}
                        </Badge>
                    )}
                    {/* Taxonomy badges */}
                    {item.taxonomy?.subject && (
                        <span className="text-[11px] text-foreground-muted px-2 py-0.5 rounded bg-surface-muted border border-border">
                            {item.taxonomy.subject}
                        </span>
                    )}
                    {item.taxonomy?.topic && (
                        <span className="text-[11px] text-foreground-muted px-2 py-0.5 rounded bg-surface-muted border border-border hidden md:inline">
                            {item.taxonomy.topic}
                        </span>
                    )}
                </div>

                <div className="flex items-center space-x-3 sm:self-center">
                    {renderEvaluationBadge()}
                    {renderMarksBadge()}
                </div>
            </div>

            {/* Question Text */}
            <div className="text-sm sm:text-base text-foreground font-medium leading-relaxed">
                {item.question_text}
            </div>

            {/* Candidate & Correct Response Content */}
            {renderTypeContent()}

            {/* Explanation & Key Concepts Section */}
            {isFinalized && item.explanation ? (
                <div className="pt-3 border-t border-border">
                    <button
                        type="button"
                        onClick={() => setIsExplanationOpen(!isExplanationOpen)}
                        className="flex items-center justify-between w-full text-left py-1 text-xs font-bold text-foreground hover:text-primary transition-colors cursor-pointer"
                    >
                        <div className="flex items-center space-x-2 text-primary-700">
                            <LightbulbIcon className="w-4 h-4 text-primary" />
                            <span>Explanation & Solution Insights</span>
                        </div>
                        {isExplanationOpen ? (
                            <ChevronUpIcon className="w-4 h-4 text-foreground-muted" />
                        ) : (
                            <ChevronDownIcon className="w-4 h-4 text-foreground-muted" />
                        )}
                    </button>

                    {isExplanationOpen && (
                        <div className="mt-2.5 p-4 rounded-xl bg-primary-50/30 border border-primary-100 text-xs sm:text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                            {item.explanation}
                        </div>
                    )}
                </div>
            ) : !isFinalized ? (
                <div className="pt-3 border-t border-border flex items-center space-x-2 text-xs text-foreground-muted">
                    <LockIcon className="w-3.5 h-3.5 shrink-0 text-foreground-muted" />
                    <span>Detailed solutions and explanations will be unlocked once manual evaluation is finalized.</span>
                </div>
            ) : null}
        </Card>
    );
};
