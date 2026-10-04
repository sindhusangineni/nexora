import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Badge } from "@/shared/ui/Badge";
import { parseApiError, type ApiError } from "@/lib/api";
import {
    QuestionForm,
    useCreateQuestion,
    type BaseQuestionCreatePayload,
} from "@/features/question-bank";

export function AdminQuestionCreatePage() {
    const navigate = useNavigate();
    const createMutation = useCreateQuestion();
    const [apiError, setApiError] = useState<ApiError | null>(null);

    const handleSubmit = async (payload: BaseQuestionCreatePayload) => {
        setApiError(null);
        try {
            const created = await createMutation.mutateAsync(payload);
            navigate(`/admin/question-bank/questions/${created.id}`);
        } catch (err) {
            setApiError(parseApiError(err));
        }
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto pb-12">
            {/* Header */}
            <div className="space-y-2 pb-4 border-b border-border">
                <Link
                    to="/admin/question-bank"
                    className="inline-flex items-center text-xs font-semibold text-primary-600 hover:text-primary-800"
                >
                    ← Back to Question Bank
                </Link>
                <div className="flex items-center gap-2 pt-1">
                    <Badge variant="primary" size="sm">
                        Authoring Workspace
                    </Badge>
                    <span className="text-xs text-foreground-muted">Initial Version v1 (DRAFT)</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                    Create Question
                </h1>
                <p className="text-sm text-foreground-muted">
                    Author a standardized question item. The initial version will begin in DRAFT status for review.
                </p>
            </div>

            {apiError && (
                <div
                    role="alert"
                    className="p-4 rounded-xl bg-red-50 border border-red-200 text-danger text-sm font-medium"
                >
                    <p className="font-semibold">{apiError.message}</p>
                    {apiError.fields && (
                        <ul className="mt-1 text-xs list-disc list-inside space-y-0.5">
                            {Object.entries(apiError.fields).map(([field, msgs]) => (
                                <li key={field}>
                                    <span className="font-semibold capitalize">{field}</span>:{" "}
                                    {msgs.join(" ")}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}

            <QuestionForm
                onSubmit={handleSubmit}
                isSubmitting={createMutation.isPending}
                submitLabel="Create Question Draft"
            />
        </div>
    );
}
