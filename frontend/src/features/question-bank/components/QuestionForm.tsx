import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/shared/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { learningApi } from "@/features/learning";
import { McqEditor } from "./editors/McqEditor";
import { MultipleSelectEditor } from "./editors/MultipleSelectEditor";
import { TrueFalseEditor } from "./editors/TrueFalseEditor";
import { AssertionReasonEditor } from "./editors/AssertionReasonEditor";
import { MatchFollowingEditor } from "./editors/MatchFollowingEditor";
import { DescriptiveEditor } from "./editors/DescriptiveEditor";
import type {
    AssertionReasonRelationship,
    BaseQuestionCreatePayload,
    ChoiceItem,
    Difficulty,
    MatchItem,
    MatchPair,
    QuestionSourceType,
    QuestionType,
} from "../types/questionBank.types";

export interface QuestionFormProps {
    initialData?: Partial<BaseQuestionCreatePayload>;
    onSubmit: (payload: BaseQuestionCreatePayload) => Promise<void>;
    isSubmitting: boolean;
    submitLabel?: string;
    isEditingDraft?: boolean;
}

export function QuestionForm({
    initialData,
    onSubmit,
    isSubmitting,
    submitLabel = "Save Draft Version",
    isEditingDraft = false,
}: QuestionFormProps) {
    // Form fields
    const [questionType, setQuestionType] = useState<QuestionType>(
        initialData?.question_type || "MCQ",
    );
    const [text, setText] = useState(initialData?.text || "");
    const [difficulty, setDifficulty] = useState<Difficulty>(
        initialData?.difficulty || "MEDIUM",
    );
    const [explanation, setExplanation] = useState(initialData?.explanation || "");
    const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>(
        initialData?.topic_ids || [],
    );

    // Provenance fields
    const [sourceType, setSourceType] = useState<QuestionSourceType | "">(
        initialData?.source_type || "",
    );
    const [sourceName, setSourceName] = useState(initialData?.source_name || "");
    const [sourceReference, setSourceReference] = useState(
        initialData?.source_reference || "",
    );
    const [sourceYear, setSourceYear] = useState<string>(
        initialData?.source_year ? String(initialData.source_year) : "",
    );
    const [externalQuestionId, setExternalQuestionId] = useState(
        initialData?.external_question_id || "",
    );

    // Type-specific contents
    const [choices, setChoices] = useState<ChoiceItem[]>(
        initialData?.choices && initialData.choices.length > 0
            ? initialData.choices
            : [
                  { text: "", position: 1, is_correct: true },
                  { text: "", position: 2, is_correct: false },
                  { text: "", position: 3, is_correct: false },
                  { text: "", position: 4, is_correct: false },
              ],
    );

    const [tfAnswer, setTfAnswer] = useState<boolean>(
        initialData?.true_false?.answer ?? true,
    );

    const [arData, setArData] = useState<{
        assertion: string;
        reason: string;
        relationship: AssertionReasonRelationship;
    }>({
        assertion: initialData?.assertion_reason?.assertion || "",
        reason: initialData?.assertion_reason?.reason || "",
        relationship:
            initialData?.assertion_reason?.correct_relationship ||
            "BOTH_TRUE_REASON_CORRECT",
    });

    const [matchData, setMatchData] = useState<{
        leftItems: MatchItem[];
        rightItems: MatchItem[];
        pairs: MatchPair[];
    }>({
        leftItems:
            initialData?.match_following?.left_items &&
            initialData.match_following.left_items.length > 0
                ? initialData.match_following.left_items.map((i, idx) => ({
                      text: i.text,
                      position: i.position || idx + 1,
                  }))
                : [
                      { text: "", position: 1 },
                      { text: "", position: 2 },
                  ],
        rightItems:
            initialData?.match_following?.right_items &&
            initialData.match_following.right_items.length > 0
                ? initialData.match_following.right_items.map((i, idx) => ({
                      text: i.text,
                      position: i.position || idx + 1,
                  }))
                : [
                      { text: "", position: 1 },
                      { text: "", position: 2 },
                  ],
        pairs:
            initialData?.match_following?.pairs || [
                { left_position: 1, right_position: 1 },
                { left_position: 2, right_position: 2 },
            ],
    });

    const [descData, setDescData] = useState<{
        marks: number;
        expectedAnswer: string;
    }>({
        marks: initialData?.descriptive?.marks || 10,
        expectedAnswer: initialData?.descriptive?.expected_answer || "",
    });

    // Validation error state
    const [clientError, setClientError] = useState<string | null>(null);

    // Fetch topics for selection
    const { data: topicsData } = useQuery({
        queryKey: ["learning", "topics-all"],
        queryFn: () => learningApi.getTopics({ page_size: 100 }),
    });

    const handleTopicToggle = (topicId: string) => {
        setSelectedTopicIds((prev) =>
            prev.includes(topicId)
                ? prev.filter((id) => id !== topicId)
                : [...prev, topicId],
        );
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setClientError(null);

        const cleanText = text.trim();
        if (!cleanText) {
            setClientError("Question text cannot be blank.");
            return;
        }

        // Validate type-specific content
        if (questionType === "MCQ") {
            if (choices.length < 2) {
                setClientError("MCQ questions require at least two choices.");
                return;
            }
            if (choices.some((c) => !c.text.trim())) {
                setClientError("All choices must contain text.");
                return;
            }
            const correctCount = choices.filter((c) => c.is_correct).length;
            if (correctCount !== 1) {
                setClientError("MCQ questions require exactly one correct choice.");
                return;
            }
        } else if (questionType === "MULTIPLE_SELECT") {
            if (choices.length < 2) {
                setClientError("Multiple select questions require at least two choices.");
                return;
            }
            if (choices.some((c) => !c.text.trim())) {
                setClientError("All choices must contain text.");
                return;
            }
            if (!choices.some((c) => c.is_correct)) {
                setClientError("At least one choice must be marked as correct.");
                return;
            }
        } else if (questionType === "ASSERTION_REASON") {
            if (!arData.assertion.trim() || !arData.reason.trim()) {
                setClientError("Both assertion and reason statements are required.");
                return;
            }
        } else if (questionType === "MATCH_FOLLOWING") {
            if (matchData.leftItems.length < 2 || matchData.rightItems.length < 2) {
                setClientError("Match following requires at least two items on each side.");
                return;
            }
            if (
                matchData.leftItems.some((i) => !i.text.trim()) ||
                matchData.rightItems.some((i) => !i.text.trim())
            ) {
                setClientError("All matching items must have non-empty text.");
                return;
            }
            if (matchData.pairs.length < matchData.leftItems.length) {
                setClientError("Every left item must have a corresponding right pair.");
                return;
            }
        } else if (questionType === "DESCRIPTIVE") {
            if (!descData.expectedAnswer.trim()) {
                setClientError("Expected answer / rubric is required for descriptive items.");
                return;
            }
        }

        const payload: BaseQuestionCreatePayload = {
            question_type: questionType,
            text: cleanText,
            difficulty,
            explanation: explanation.trim(),
            topic_ids: selectedTopicIds,
            source_type: (sourceType as QuestionSourceType) || null,
            source_name: sourceName.trim() || null,
            source_reference: sourceReference.trim() || null,
            source_year: sourceYear ? parseInt(sourceYear, 10) : null,
            external_question_id: externalQuestionId.trim() || null,
        };

        // Attach mutually exclusive content
        if (questionType === "MCQ" || questionType === "MULTIPLE_SELECT") {
            payload.choices = choices.map((c, idx) => ({
                text: c.text.trim(),
                position: idx + 1,
                is_correct: Boolean(c.is_correct),
            }));
        } else if (questionType === "TRUE_FALSE") {
            payload.true_false = { answer: tfAnswer };
        } else if (questionType === "ASSERTION_REASON") {
            payload.assertion_reason = {
                assertion: arData.assertion.trim(),
                reason: arData.reason.trim(),
                correct_relationship: arData.relationship,
            };
        } else if (questionType === "MATCH_FOLLOWING") {
            payload.match_following = {
                left_items: matchData.leftItems.map((i, idx) => ({
                    text: i.text.trim(),
                    position: idx + 1,
                })),
                right_items: matchData.rightItems.map((i, idx) => ({
                    text: i.text.trim(),
                    position: idx + 1,
                })),
                pairs: matchData.pairs,
            };
        } else if (questionType === "DESCRIPTIVE") {
            payload.descriptive = {
                marks: descData.marks,
                expected_answer: descData.expectedAnswer.trim(),
            };
        }

        await onSubmit(payload);
    };

    const questionTypes: Array<{ type: QuestionType; label: string }> = [
        { type: "MCQ", label: "Multiple Choice (Single)" },
        { type: "MULTIPLE_SELECT", label: "Multiple Select" },
        { type: "TRUE_FALSE", label: "True / False" },
        { type: "ASSERTION_REASON", label: "Assertion & Reason" },
        { type: "MATCH_FOLLOWING", label: "Match the Following" },
        { type: "DESCRIPTIVE", label: "Descriptive Essay" },
    ];

    return (
        <form onSubmit={handleSubmit} className="space-y-8" noValidate>
            {clientError && (
                <div
                    role="alert"
                    className="p-4 rounded-xl bg-red-50 border border-red-200 text-danger text-sm font-medium"
                >
                    {clientError}
                </div>
            )}

            {/* Section 1: Core Details */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>1. Question Details</CardTitle>
                        <Badge variant="primary" size="sm">
                            Step 1 of 4
                        </Badge>
                    </div>
                    <CardDescription>
                        Define the format, difficulty, and primary stem for this question.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                    {/* Question Type Selector */}
                    <div className="space-y-2">
                        <label className="block text-xs font-semibold uppercase tracking-wider text-foreground">
                            Question Type
                        </label>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                            {questionTypes.map((qt) => (
                                <button
                                    key={qt.type}
                                    type="button"
                                    onClick={() => setQuestionType(qt.type)}
                                    disabled={isEditingDraft || isSubmitting}
                                    className={`p-3 rounded-lg border text-left text-xs font-semibold transition-all ${
                                        questionType === qt.type
                                            ? "bg-primary-50 border-primary-500 text-primary-900 ring-2 ring-primary-500/20 shadow-xs"
                                            : "bg-surface border-border text-foreground-muted hover:border-neutral-300 hover:text-foreground"
                                    } disabled:opacity-50`}
                                >
                                    {qt.label}
                                </button>
                            ))}
                        </div>
                        {isEditingDraft && (
                            <p className="text-[11px] text-neutral-400">
                                Question type cannot be changed on an existing version.
                            </p>
                        )}
                    </div>

                    {/* Difficulty & Marks */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label
                                htmlFor="q-difficulty"
                                className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                            >
                                Difficulty
                            </label>
                            <select
                                id="q-difficulty"
                                value={difficulty}
                                onChange={(e) => setDifficulty(e.target.value as Difficulty)}
                                disabled={isSubmitting}
                                className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50"
                            >
                                <option value="EASY">Easy</option>
                                <option value="MEDIUM">Medium</option>
                                <option value="HARD">Hard</option>
                            </select>
                        </div>
                    </div>

                    {/* Question Stem Text */}
                    <div className="space-y-1.5">
                        <label
                            htmlFor="q-text"
                            className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                        >
                            Question Stem / Prompt Text <span className="text-danger">*</span>
                        </label>
                        <textarea
                            id="q-text"
                            rows={4}
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            disabled={isSubmitting}
                            placeholder="Enter the primary question text clearly..."
                            className="w-full p-3.5 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 leading-relaxed"
                        />
                    </div>

                    {/* Pedagogical Explanation */}
                    <div className="space-y-1.5">
                        <label
                            htmlFor="q-explanation"
                            className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                        >
                            Pedagogical Explanation (Admin / Post-Exam Feedback)
                        </label>
                        <textarea
                            id="q-explanation"
                            rows={3}
                            value={explanation}
                            onChange={(e) => setExplanation(e.target.value)}
                            disabled={isSubmitting}
                            placeholder="Provide conceptual justification, statutory references, or background context..."
                            className="w-full p-3 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 leading-relaxed"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Section 2: Type-Specific Content Editor */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>2. Question Content & Answer Key</CardTitle>
                        <Badge variant="primary" size="sm">
                            Step 2 of 4
                        </Badge>
                    </div>
                    <CardDescription>
                        Configure type-specific options, pairs, or rubrics for {questionType}.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {questionType === "MCQ" && (
                        <McqEditor
                            choices={choices}
                            onChange={setChoices}
                            disabled={isSubmitting}
                        />
                    )}
                    {questionType === "MULTIPLE_SELECT" && (
                        <MultipleSelectEditor
                            choices={choices}
                            onChange={setChoices}
                            disabled={isSubmitting}
                        />
                    )}
                    {questionType === "TRUE_FALSE" && (
                        <TrueFalseEditor
                            answer={tfAnswer}
                            onChange={setTfAnswer}
                            disabled={isSubmitting}
                        />
                    )}
                    {questionType === "ASSERTION_REASON" && (
                        <AssertionReasonEditor
                            assertion={arData.assertion}
                            reason={arData.reason}
                            relationship={arData.relationship}
                            onChange={setArData}
                            disabled={isSubmitting}
                        />
                    )}
                    {questionType === "MATCH_FOLLOWING" && (
                        <MatchFollowingEditor
                            leftItems={matchData.leftItems}
                            rightItems={matchData.rightItems}
                            pairs={matchData.pairs}
                            onChange={setMatchData}
                            disabled={isSubmitting}
                        />
                    )}
                    {questionType === "DESCRIPTIVE" && (
                        <DescriptiveEditor
                            marks={descData.marks}
                            expectedAnswer={descData.expectedAnswer}
                            onChange={setDescData}
                            disabled={isSubmitting}
                        />
                    )}
                </CardContent>
            </Card>

            {/* Section 3: Topic Association */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>3. Curriculum Topic Tagging</CardTitle>
                        <Badge variant="primary" size="sm">
                            Step 3 of 4
                        </Badge>
                    </div>
                    <CardDescription>
                        Tag this question to one or more curriculum topics for granular syllabus mastery.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {topicsData && topicsData.results.length > 0 ? (
                        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-2 border border-border rounded-lg bg-surface-muted/30">
                            {topicsData.results.map((topic) => {
                                const isSelected = selectedTopicIds.includes(topic.id);
                                return (
                                    <button
                                        key={topic.id}
                                        type="button"
                                        onClick={() => handleTopicToggle(topic.id)}
                                        disabled={isSubmitting}
                                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                                            isSelected
                                                ? "bg-primary-600 text-white border-primary-600 shadow-xs"
                                                : "bg-surface text-neutral-700 border-border hover:border-neutral-300"
                                        }`}
                                    >
                                        {isSelected ? "✓ " : "+ "}
                                        {topic.name}
                                    </button>
                                );
                            })}
                        </div>
                    ) : (
                        <p className="text-xs text-foreground-muted">
                            Loading curriculum topics...
                        </p>
                    )}
                    <p className="text-xs text-foreground-muted">
                        Selected: {selectedTopicIds.length} topic(s)
                    </p>
                </CardContent>
            </Card>

            {/* Section 4: Provenance Metadata */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>4. Provenance & Attribution</CardTitle>
                        <Badge variant="default" size="sm">
                            Optional
                        </Badge>
                    </div>
                    <CardDescription>
                        Record source origin, examination reference, and year for auditing.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label
                                htmlFor="p-source-type"
                                className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                            >
                                Source Type
                            </label>
                            <select
                                id="p-source-type"
                                value={sourceType}
                                onChange={(e) =>
                                    setSourceType(
                                        (e.target.value as QuestionSourceType) || "",
                                    )
                                }
                                disabled={isSubmitting}
                                className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50"
                            >
                                <option value="">None / Unspecified</option>
                                <option value="ORIGINAL">Original Content</option>
                                <option value="UPSC_PREVIOUS_YEAR">UPSC Previous Year</option>
                                <option value="LICENSED">Licensed Material</option>
                                <option value="CONTRIBUTOR">External Contributor</option>
                                <option value="AI_GENERATED">AI Generated Draft</option>
                                <option value="IMPORTED">Imported Dataset</option>
                            </select>
                        </div>

                        <div className="space-y-1.5">
                            <label
                                htmlFor="p-source-year"
                                className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                            >
                                Examination / Source Year
                            </label>
                            <input
                                id="p-source-year"
                                type="number"
                                min={1900}
                                max={2100}
                                value={sourceYear}
                                onChange={(e) => setSourceYear(e.target.value)}
                                disabled={isSubmitting}
                                placeholder="e.g. 2024"
                                className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label
                                htmlFor="p-source-name"
                                className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                            >
                                Source Name
                            </label>
                            <input
                                id="p-source-name"
                                type="text"
                                value={sourceName}
                                onChange={(e) => setSourceName(e.target.value)}
                                disabled={isSubmitting}
                                placeholder="e.g. UPSC Civil Services Prelims"
                                className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label
                                htmlFor="p-source-ref"
                                className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                            >
                                Citation / Paper Reference
                            </label>
                            <input
                                id="p-source-ref"
                                type="text"
                                value={sourceReference}
                                onChange={(e) => setSourceReference(e.target.value)}
                                disabled={isSubmitting}
                                placeholder="e.g. GS Paper I, Q-42 (Series A)"
                                className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50"
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5 max-w-sm">
                        <label
                            htmlFor="p-ext-id"
                            className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                        >
                            External Question Identifier
                        </label>
                        <input
                            id="p-ext-id"
                            type="text"
                            value={externalQuestionId}
                            onChange={(e) => setExternalQuestionId(e.target.value)}
                            disabled={isSubmitting}
                            placeholder="e.g. EXT-2024-POL-042"
                            className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 font-mono text-xs"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Submit Bar */}
            <div className="flex items-center justify-end gap-4 p-4 rounded-xl border border-border bg-surface">
                <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    loading={isSubmitting}
                    disabled={isSubmitting || !text.trim()}
                >
                    {submitLabel}
                </Button>
            </div>
        </form>
    );
}
