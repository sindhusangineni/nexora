import React, { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import {
    AssessmentLifecycleActions,
    AssessmentReview,
    AssessmentStatusBadge,
    AssessmentTypeBadge,
    MarkingTimingConfiguration,
    SectionManager,
    SelectionRuleList,
    useAssessment,
    useAssessmentSections,
    useSelectionRules,
    useUpdateAssessment,
    type Assessment,
    type AssessmentSection,
    type AssessmentStatus,
    type AssessmentType,
    type ScoreFloorPolicy,
    type SelectionRule,
} from "@/features/assessment";

interface AssessmentEditorContentProps {
    assessment: Assessment;
    sections: AssessmentSection[];
    rules: SelectionRule[];
}

const AssessmentEditorContent: React.FC<AssessmentEditorContentProps> = ({
    assessment,
    sections,
    rules,
}) => {
    const navigate = useNavigate();
    const updateMutation = useUpdateAssessment(assessment.id);

    // Active tab: "details" | "timing" | "sections" | "rules" | "review"
    const [activeTab, setActiveTab] = useState<
        "details" | "timing" | "sections" | "rules" | "review"
    >("details");

    // Form fields initialized directly from assessment
    const [title, setTitle] = useState(assessment.title);
    const [description, setDescription] = useState(assessment.description || "");
    const [type, setType] = useState<AssessmentType>(assessment.type);
    const [durationMinutes, setDurationMinutes] = useState<number>(
        Math.round(assessment.duration_seconds / 60),
    );
    const [marksPerQuestion, setMarksPerQuestion] = useState<string>(
        assessment.marks_per_question,
    );
    const [penaltyPerQuestion, setPenaltyPerQuestion] = useState<string>(
        assessment.penalty_per_question,
    );
    const [scoreFloorPolicy, setScoreFloorPolicy] =
        useState<ScoreFloorPolicy>("UNRESTRICTED");

    const [saveSuccess, setSaveSuccess] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    const handleSaveDetails = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaveError(null);
        setSaveSuccess(false);

        const durationSeconds = durationMinutes * 60;
        const marks = parseFloat(marksPerQuestion);
        const penalty = parseFloat(penaltyPerQuestion);

        if (!title.trim()) {
            setSaveError("Title cannot be empty.");
            return;
        }
        if (durationSeconds < 1) {
            setSaveError("Duration must be at least 1 minute.");
            return;
        }
        if (isNaN(marks) || marks <= 0) {
            setSaveError("Marks per question must be greater than 0.");
            return;
        }
        if (isNaN(penalty) || penalty < 0) {
            setSaveError("Penalty per question cannot be negative.");
            return;
        }

        try {
            await updateMutation.mutateAsync({
                title: title.trim(),
                description: description.trim(),
                type,
                duration_seconds: durationSeconds,
                marks_per_question: marks.toFixed(2),
                penalty_per_question: penalty.toFixed(2),
            });
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
        } catch (err: unknown) {
            const message =
                err instanceof Error ? err.message : "Failed to update assessment.";
            setSaveError(message);
        }
    };

    return (
        <div className="space-y-6">
            {/* Breadcrumb */}
            <div className="flex items-center space-x-2 text-xs text-foreground-muted">
                <Link
                    to="/admin/assessments"
                    className="hover:text-foreground transition-colors"
                >
                    Assessments
                </Link>
                <span>/</span>
                <Link
                    to={`/admin/assessments/${assessment.id}`}
                    className="hover:text-foreground transition-colors truncate max-w-xs"
                >
                    {assessment.title}
                </Link>
                <span>/</span>
                <span className="text-foreground font-medium">Builder</span>
            </div>

            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
                <div>
                    <div className="flex items-center space-x-2.5">
                        <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                            Assessment Builder
                        </h1>
                        <AssessmentStatusBadge
                            status={assessment.status as AssessmentStatus}
                        />
                        <AssessmentTypeBadge
                            type={assessment.type as AssessmentType}
                        />
                    </div>
                    <p className="text-xs text-foreground-muted mt-1">
                        Editing draft specification for {assessment.title}
                    </p>
                </div>

                <div className="flex items-center space-x-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => navigate(`/admin/assessments/${assessment.id}`)}
                    >
                        Done & View
                    </Button>
                </div>
            </div>

            {saveSuccess && (
                <div className="p-3 bg-success-surface border border-success/20 rounded-md text-xs text-success font-medium">
                    Changes saved successfully.
                </div>
            )}

            {saveError && (
                <div className="p-3 bg-danger-surface border border-danger/20 rounded-md text-xs text-danger">
                    {saveError}
                </div>
            )}

            {/* Tab navigation */}
            <div className="flex space-x-1 border-b border-border overflow-x-auto">
                <button
                    type="button"
                    onClick={() => setActiveTab("details")}
                    className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
                        activeTab === "details"
                            ? "border-primary text-primary"
                            : "border-transparent text-foreground-muted hover:text-foreground"
                    }`}
                >
                    1. Details
                </button>
                <button
                    type="button"
                    onClick={() => setActiveTab("timing")}
                    className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
                        activeTab === "timing"
                            ? "border-primary text-primary"
                            : "border-transparent text-foreground-muted hover:text-foreground"
                    }`}
                >
                    2. Timing & Marking
                </button>
                <button
                    type="button"
                    onClick={() => setActiveTab("sections")}
                    className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
                        activeTab === "sections"
                            ? "border-primary text-primary"
                            : "border-transparent text-foreground-muted hover:text-foreground"
                    }`}
                >
                    3. Sections ({sections.length})
                </button>
                <button
                    type="button"
                    onClick={() => setActiveTab("rules")}
                    className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
                        activeTab === "rules"
                            ? "border-primary text-primary"
                            : "border-transparent text-foreground-muted hover:text-foreground"
                    }`}
                >
                    4. Selection Rules ({rules.length})
                </button>
                <button
                    type="button"
                    onClick={() => setActiveTab("review")}
                    className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
                        activeTab === "review"
                            ? "border-primary text-primary"
                            : "border-transparent text-foreground-muted hover:text-foreground"
                    }`}
                >
                    5. Review & Publish
                </button>
            </div>

            {/* Tab Panels */}
            {activeTab === "details" && (
                <Card className="p-6">
                    <form onSubmit={handleSaveDetails} className="space-y-5">
                        <Input
                            label="Assessment Title"
                            required
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />

                        <div>
                            <label
                                htmlFor="edit-assessment-desc"
                                className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                            >
                                Description (Optional)
                            </label>
                            <textarea
                                id="edit-assessment-desc"
                                rows={4}
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full px-3 py-2 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="edit-assessment-type"
                                className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1"
                            >
                                Assessment Type
                            </label>
                            <select
                                id="edit-assessment-type"
                                value={type}
                                onChange={(e) => setType(e.target.value as AssessmentType)}
                                className="w-full h-10 px-3 border border-border rounded-md bg-surface text-foreground text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            >
                                <option value="PRACTICE">Practice</option>
                                <option value="REVISION">Revision</option>
                                <option value="MOCK">Mock</option>
                                <option value="CUSTOM">Custom</option>
                            </select>
                        </div>

                        <div className="flex justify-end pt-3 border-t border-border">
                            <Button
                                type="submit"
                                variant="primary"
                                loading={updateMutation.isPending}
                            >
                                Save Details
                            </Button>
                        </div>
                    </form>
                </Card>
            )}

            {activeTab === "timing" && (
                <Card className="p-6">
                    <form onSubmit={handleSaveDetails} className="space-y-6">
                        <MarkingTimingConfiguration
                            durationMinutes={durationMinutes}
                            onDurationMinutesChange={setDurationMinutes}
                            marksPerQuestion={marksPerQuestion}
                            onMarksPerQuestionChange={setMarksPerQuestion}
                            penaltyPerQuestion={penaltyPerQuestion}
                            onPenaltyPerQuestionChange={setPenaltyPerQuestion}
                            scoreFloorPolicy={scoreFloorPolicy}
                            onScoreFloorPolicyChange={setScoreFloorPolicy}
                        />

                        <div className="flex justify-end pt-4 border-t border-border">
                            <Button
                                type="submit"
                                variant="primary"
                                loading={updateMutation.isPending}
                            >
                                Save Configuration
                            </Button>
                        </div>
                    </form>
                </Card>
            )}

            {activeTab === "sections" && (
                <Card className="p-6">
                    <SectionManager
                        assessmentId={assessment.id}
                        sections={sections}
                        isDraft={true}
                    />
                </Card>
            )}

            {activeTab === "rules" && (
                <Card className="p-6">
                    <SelectionRuleList
                        assessmentId={assessment.id}
                        rules={rules}
                        sections={sections}
                        isDraft={true}
                    />
                </Card>
            )}

            {activeTab === "review" && (
                <div className="space-y-6">
                    <Card className="p-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div>
                                <h3 className="text-base font-semibold text-foreground">
                                    Publish Assessment
                                </h3>
                                <p className="text-xs text-foreground-muted mt-0.5">
                                    Transition this assessment from DRAFT to PUBLISHED to lock configuration and enable paper generation.
                                </p>
                            </div>
                            <AssessmentLifecycleActions
                                assessment={assessment}
                                rules={rules}
                            />
                        </div>
                    </Card>

                    <AssessmentReview
                        assessment={assessment}
                        sections={sections}
                        rules={rules}
                        scoreFloorPolicy={scoreFloorPolicy}
                    />
                </div>
            )}
        </div>
    );
};

export const AdminAssessmentEditPage: React.FC = () => {
    const { assessmentId } = useParams<{ assessmentId: string }>();
    const navigate = useNavigate();

    const {
        data: assessment,
        isLoading: isLoadingAssessment,
        error: assessmentError,
    } = useAssessment(assessmentId || "");

    const { data: sections = [], isLoading: isLoadingSections } =
        useAssessmentSections(assessmentId || "");

    const { data: rules = [], isLoading: isLoadingRules } =
        useSelectionRules(assessmentId || "");

    if (isLoadingAssessment || isLoadingSections || isLoadingRules) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-10 w-3/4" />
                <Skeleton className="h-64" />
            </div>
        );
    }

    if (assessmentError || !assessment) {
        return (
            <div className="p-6 bg-danger-surface border border-danger/20 rounded-lg text-danger space-y-3">
                <h3 className="font-semibold text-base">Assessment Not Found</h3>
                <p className="text-sm">The assessment could not be loaded.</p>
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate("/admin/assessments")}
                >
                    Back to Assessments
                </Button>
            </div>
        );
    }

    // Immutable check
    if (assessment.status !== "DRAFT") {
        return (
            <div className="space-y-6">
                <div className="p-6 bg-warning-surface border border-warning/20 rounded-lg text-neutral-900 space-y-3">
                    <h3 className="font-semibold text-base">
                        Assessment is Immutable
                    </h3>
                    <p className="text-sm text-foreground-muted">
                        This assessment is currently in{" "}
                        <strong className="text-neutral-900">{assessment.status}</strong> status.
                        Published and archived assessments cannot be modified to preserve historical integrity.
                    </p>
                    <div className="pt-2">
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() =>
                                navigate(`/admin/assessments/${assessment.id}`)
                            }
                        >
                            View Assessment Specification
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <AssessmentEditorContent
            key={assessment.id}
            assessment={assessment}
            sections={sections}
            rules={rules}
        />
    );
};
