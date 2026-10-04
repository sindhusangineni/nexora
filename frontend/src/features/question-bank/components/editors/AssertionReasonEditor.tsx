import type { AssertionReasonRelationship } from "../../types/questionBank.types";

export interface AssertionReasonEditorProps {
    assertion: string;
    reason: string;
    relationship: AssertionReasonRelationship;
    onChange: (data: {
        assertion: string;
        reason: string;
        relationship: AssertionReasonRelationship;
    }) => void;
    disabled?: boolean;
    errors?: {
        assertion?: string;
        reason?: string;
        relationship?: string;
    };
}

export function AssertionReasonEditor({
    assertion,
    reason,
    relationship,
    onChange,
    disabled = false,
    errors,
}: AssertionReasonEditorProps) {
    const relationships: Array<{
        value: AssertionReasonRelationship;
        label: string;
        short: string;
    }> = [
        {
            value: "BOTH_TRUE_REASON_CORRECT",
            short: "Both True & R explains A",
            label: "Both Assertion (A) and Reason (R) are true, and (R) is the correct explanation of (A)",
        },
        {
            value: "BOTH_TRUE_REASON_NOT_CORRECT",
            short: "Both True & R does NOT explain A",
            label: "Both Assertion (A) and Reason (R) are true, but (R) is NOT the correct explanation of (A)",
        },
        {
            value: "ASSERTION_TRUE_REASON_FALSE",
            short: "A is True, R is False",
            label: "Assertion (A) is true, but Reason (R) is false",
        },
        {
            value: "ASSERTION_FALSE_REASON_FALSE",
            short: "Both False",
            label: "Assertion (A) is false, and Reason (R) is false",
        },
    ];

    return (
        <div className="space-y-4">
            <div>
                <h4 className="text-sm font-semibold text-foreground tracking-tight">
                    Assertion & Reason Statements
                </h4>
                <p className="text-xs text-foreground-muted">
                    Formulate two distinct statements and specify their logical relationship.
                </p>
            </div>

            {/* Assertion Statement */}
            <div className="space-y-1.5">
                <label
                    htmlFor="ar-assertion"
                    className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                >
                    Assertion (A)
                </label>
                <textarea
                    id="ar-assertion"
                    rows={2}
                    value={assertion}
                    onChange={(e) =>
                        onChange({ assertion: e.target.value, reason, relationship })
                    }
                    disabled={disabled}
                    placeholder="State the assertion clearly..."
                    className={`w-full p-3 text-sm rounded-lg border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 ${
                        errors?.assertion ? "border-danger" : "border-border"
                    }`}
                />
                {errors?.assertion && (
                    <p className="text-xs font-medium text-danger" role="alert">
                        {errors.assertion}
                    </p>
                )}
            </div>

            {/* Reason Statement */}
            <div className="space-y-1.5">
                <label
                    htmlFor="ar-reason"
                    className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                >
                    Reason (R)
                </label>
                <textarea
                    id="ar-reason"
                    rows={2}
                    value={reason}
                    onChange={(e) =>
                        onChange({ assertion, reason: e.target.value, relationship })
                    }
                    disabled={disabled}
                    placeholder="State the accompanying reason or explanation..."
                    className={`w-full p-3 text-sm rounded-lg border bg-surface text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 ${
                        errors?.reason ? "border-danger" : "border-border"
                    }`}
                />
                {errors?.reason && (
                    <p className="text-xs font-medium text-danger" role="alert">
                        {errors.reason}
                    </p>
                )}
            </div>

            {/* Correct Relationship */}
            <div className="space-y-1.5">
                <label
                    htmlFor="ar-relationship"
                    className="block text-xs font-semibold uppercase tracking-wider text-foreground"
                >
                    Evaluated Relationship
                </label>
                <select
                    id="ar-relationship"
                    value={relationship}
                    onChange={(e) =>
                        onChange({
                            assertion,
                            reason,
                            relationship: e.target.value as AssertionReasonRelationship,
                        })
                    }
                    disabled={disabled}
                    className={`w-full h-10 px-3 text-sm rounded-lg border bg-surface text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-600 disabled:opacity-50 ${
                        errors?.relationship ? "border-danger" : "border-border"
                    }`}
                >
                    {relationships.map((r) => (
                        <option key={r.value} value={r.value}>
                            {r.label}
                        </option>
                    ))}
                </select>
                {errors?.relationship && (
                    <p className="text-xs font-medium text-danger" role="alert">
                        {errors.relationship}
                    </p>
                )}
            </div>
        </div>
    );
}
