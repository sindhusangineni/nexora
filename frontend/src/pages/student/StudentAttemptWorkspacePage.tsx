import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
    useAttempt,
    useAttemptPaper,
    useAttemptAssessment,
    useAttemptSections,
    useSaveResponse,
    useClearResponse,
    useSubmitAttempt,
} from "@/features/attempts";
import { AttemptWorkspace } from "@/features/attempts/components/AttemptWorkspace";
import { Skeleton } from "@/shared/ui/Skeleton";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { AlertCircleIcon } from "@/features/attempts/components/Icons";
import type { SaveResponsePayload } from "@/features/attempts/types/attempt.types";

export const StudentAttemptWorkspacePage: React.FC = () => {
    const { attemptId } = useParams<{ attemptId: string }>();
    const navigate = useNavigate();

    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const {
        data: attempt,
        isLoading: isAttemptLoading,
        error: attemptError,
        refetch: refetchAttempt,
    } = useAttempt(attemptId || "", { enabled: !!attemptId });

    const { data: paper } = useAttemptPaper(attempt?.assessment_paper_id);
    const { data: assessment } = useAttemptAssessment(paper?.assessment_id);
    const { data: sections } = useAttemptSections(paper?.assessment_id);

    const saveMutation = useSaveResponse(attemptId || "");
    const clearMutation = useClearResponse(attemptId || "");
    const submitMutation = useSubmitAttempt(attemptId || "");

    if (isAttemptLoading) {
        return (
            <div className="min-h-screen bg-background p-6 space-y-6 max-w-7xl mx-auto">
                <div className="flex items-center justify-between border-b pb-4">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-8 w-32" />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    <div className="lg:col-span-8">
                        <Skeleton className="h-96 w-full rounded-lg" />
                    </div>
                    <div className="lg:col-span-4">
                        <Skeleton className="h-64 w-full rounded-lg" />
                    </div>
                </div>
            </div>
        );
    }

    if (attemptError || !attempt) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <Card className="max-w-md w-full p-6 text-center space-y-4">
                    <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 mx-auto flex items-center justify-center">
                        <AlertCircleIcon className="w-6 h-6" />
                    </div>
                    <h2 className="text-lg font-bold text-neutral-900">
                        Unable to Load Attempt
                    </h2>
                    <p className="text-xs text-foreground-muted leading-relaxed">
                        {attemptError?.message || "The requested attempt could not be found or access is restricted."}
                    </p>
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => navigate("/student/assessments")}
                        className="w-full"
                    >
                        Back to Assessments
                    </Button>
                </Card>
            </div>
        );
    }

    const handleSave = async (itemId: string, payload: SaveResponsePayload) => {
        setErrorMsg(null);
        await saveMutation.mutateAsync({ itemId, payload });
    };

    const handleClear = async (itemId: string) => {
        setErrorMsg(null);
        await clearMutation.mutateAsync({ itemId });
    };

    const handleSubmit = async () => {
        try {
            const result = await submitMutation.mutateAsync();
            navigate(`/student/attempts/${result.id}/result`);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to submit attempt";
            setErrorMsg(msg);
            await refetchAttempt();
        }
    };

    return (
        <div>
            {errorMsg && (
                <div className="bg-red-50 text-red-800 text-xs px-4 py-2 border-b border-red-200 text-center font-medium">
                    {errorMsg}
                </div>
            )}
            <AttemptWorkspace
                attempt={attempt}
                assessment={assessment}
                sections={sections}
                paper={paper}
                onSaveResponse={handleSave}
                onClearResponse={handleClear}
                onSubmitAttempt={handleSubmit}
                onExpireReconcile={() => {
                    refetchAttempt();
                }}
                isSubmitting={submitMutation.isPending}
            />
        </div>
    );
};
