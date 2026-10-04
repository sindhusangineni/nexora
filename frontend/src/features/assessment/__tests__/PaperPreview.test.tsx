import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { PaperPreview } from "../components/PaperPreview";
import type {
    Assessment,
    AssessmentPaper,
    AssessmentSection,
} from "../types/assessment.types";

describe("PaperPreview", () => {
    const dummyAssessment: Assessment = {
        id: "asm-1",
        title: "UPSC Prelims Mock 01",
        description: "Full length mock test",
        type: "MOCK",
        status: "PUBLISHED",
        duration_seconds: 7200,
        marks_per_question: "2.00",
        penalty_per_question: "0.66",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
    };

    const dummySections: AssessmentSection[] = [
        {
            id: "sec-1",
            assessment_id: "asm-1",
            title: "General Studies",
            description: "",
            position: 0,
            created_at: "",
            updated_at: "",
        },
    ];

    const dummyPaper: AssessmentPaper = {
        id: "paper-9999-uuid",
        assessment_id: "asm-1",
        status: "GENERATED",
        duration_seconds: 7200,
        marks_per_question: "2.00",
        penalty_per_question: "0.66",
        created_at: new Date().toISOString(),
        items: [
            {
                id: "pi-1",
                paper_id: "paper-9999-uuid",
                question_id: "q-uuid-1",
                question_version_id: "qv-uuid-1",
                assessment_section_id: "sec-1",
                presentation_order: 1,
                allocated_marks: "2.00",
                allocated_penalty: "0.66",
                created_at: new Date().toISOString(),
            },
            {
                id: "pi-2",
                paper_id: "paper-9999-uuid",
                question_id: "q-uuid-2",
                question_version_id: "qv-uuid-2",
                assessment_section_id: null,
                presentation_order: 2,
                allocated_marks: "2.00",
                allocated_penalty: "0.66",
                created_at: new Date().toISOString(),
            },
        ],
    };

    it("renders immutable snapshot banner and paper details", () => {
        render(
            <PaperPreview
                paper={dummyPaper}
                assessment={dummyAssessment}
                sections={dummySections}
            />,
        );

        expect(
            screen.getByText(/immutable test paper artifact/i),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/this paper is an immutable snapshot/i),
        ).toBeInTheDocument();

        expect(screen.getByText("UPSC Prelims Mock 01")).toBeInTheDocument();
        expect(screen.getByText("120 minutes")).toBeInTheDocument();
        expect(screen.getByText("+2.00 / -0.66")).toBeInTheDocument();
    });

    it("displays questions in presentation sequence with pinned versions and marks", () => {
        render(
            <PaperPreview
                paper={dummyPaper}
                assessment={dummyAssessment}
                sections={dummySections}
            />,
        );

        expect(screen.getByText("1")).toBeInTheDocument();
        expect(screen.getByText("2")).toBeInTheDocument();

        expect(screen.getByText(/Section: General Studies/i)).toBeInTheDocument();
        expect(screen.getByText("q-uuid-1")).toBeInTheDocument();
        expect(screen.getByText("qv-uuid-1")).toBeInTheDocument();

        expect(screen.getByText("q-uuid-2")).toBeInTheDocument();
        expect(screen.getByText("qv-uuid-2")).toBeInTheDocument();
    });
});
