import React from "react";
import { Link } from "react-router-dom";
import { AssessmentForm } from "@/features/assessment";

export const AdminAssessmentCreatePage: React.FC = () => {
    return (
        <div className="space-y-6">
            <div className="flex items-center space-x-2 text-xs text-foreground-muted">
                <Link
                    to="/admin/assessments"
                    className="hover:text-foreground transition-colors"
                >
                    Assessments
                </Link>
                <span>/</span>
                <span className="text-foreground font-medium">New Assessment</span>
            </div>

            <div>
                <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                    Create New Assessment
                </h1>
                <p className="text-sm text-foreground-muted mt-1">
                    Initialize an assessment definition. You will be able to configure sections and question selection rules once the draft is created.
                </p>
            </div>

            <AssessmentForm />
        </div>
    );
};
