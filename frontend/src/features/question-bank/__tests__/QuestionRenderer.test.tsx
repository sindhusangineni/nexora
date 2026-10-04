import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
    QuestionRenderer,
    type StudentSafeQuestionData,
} from "../components/delivery/QuestionRenderer";

describe("QuestionRenderer (Student Safe Delivery)", () => {
    describe("MCQ Rendering & Safety", () => {
        const mcqQuestion: StudentSafeQuestionData = {
            id: "v-mcq-1",
            question_type: "MCQ",
            text: "Which Article of the Constitution guarantees the Right to Equality?",
            content: {
                choices: [
                    { id: "c-1", text: "Article 14", position: 1 },
                    { id: "c-2", text: "Article 19", position: 2 },
                    { id: "c-3", text: "Article 21", position: 3 },
                    { id: "c-4", text: "Article 32", position: 4 },
                ],
            },
        };

        it("renders sanitized MCQ without any answer keys or correct indicators", () => {
            render(
                <QuestionRenderer
                    question={mcqQuestion}
                    value={null}
                    onChange={vi.fn()}
                />,
            );

            expect(
                screen.getByText(
                    "Which Article of the Constitution guarantees the Right to Equality?",
                ),
            ).toBeInTheDocument();
            expect(screen.getByText("Article 14")).toBeInTheDocument();
            expect(screen.getByText("Article 32")).toBeInTheDocument();

            // SECURITY ASSERTIONS: No answer key, rubric, explanation, or lifecycle badges
            expect(screen.queryByText(/is_correct/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/explanation/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/correct answer/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/rubric/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/published/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/draft/i)).not.toBeInTheDocument();
        });

        it("allows student to select a choice", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <QuestionRenderer
                    question={mcqQuestion}
                    value={null}
                    onChange={onChange}
                />,
            );

            const radios = screen.getAllByRole("radio");
            expect(radios).toHaveLength(4);

            await user.click(radios[0]);
            expect(onChange).toHaveBeenCalledWith("c-1");
        });
    });

    describe("Multiple Select Rendering & Safety", () => {
        const msQuestion: StudentSafeQuestionData = {
            id: "v-ms-1",
            question_type: "MULTIPLE_SELECT",
            text: "Which of the following are Fundamental Duties under Article 51A?",
            content: {
                choices: [
                    { id: "c-1", text: "To safeguard public property", position: 1 },
                    { id: "c-2", text: "To develop scientific temper", position: 2 },
                    { id: "c-3", text: "To vote in elections", position: 3 },
                ],
            },
        };

        it("renders checkbox choices and allows multi-selection", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <QuestionRenderer
                    question={msQuestion}
                    value={["c-1"]}
                    onChange={onChange}
                />,
            );

            expect(
                screen.getByText("To safeguard public property"),
            ).toBeInTheDocument();

            const checkboxes = screen.getAllByRole("checkbox");
            expect(checkboxes).toHaveLength(3);

            // Click second option to toggle selection
            await user.click(checkboxes[1]);

            expect(onChange).toHaveBeenCalledWith(["c-1", "c-2"]);
        });
    });

    describe("True / False Rendering", () => {
        const tfQuestion: StudentSafeQuestionData = {
            id: "v-tf-1",
            question_type: "TRUE_FALSE",
            text: "The Rajya Sabha is subject to dissolution.",
        };

        it("renders True and False selection buttons without leaking correct value", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <QuestionRenderer
                    question={tfQuestion}
                    value={null}
                    onChange={onChange}
                />,
            );

            const trueBtn = screen.getByRole("button", { name: /true/i });
            const falseBtn = screen.getByRole("button", { name: /false/i });

            expect(trueBtn).toBeInTheDocument();
            expect(falseBtn).toBeInTheDocument();

            await user.click(falseBtn);
            expect(onChange).toHaveBeenCalledWith(false);

            // SECURITY ASSERTIONS: Neither answer nor explanation leaked
            expect(screen.queryByText(/is_correct/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/explanation/i)).not.toBeInTheDocument();
        });
    });

    describe("Assertion Reason Rendering", () => {
        const arQuestion: StudentSafeQuestionData = {
            id: "v-ar-1",
            question_type: "ASSERTION_REASON",
            text: "Assess the given assertion and reason.",
            content: {
                assertion: "Money Bills cannot be introduced in the Rajya Sabha.",
                reason: "Lok Sabha is the directly elected chamber representing the people.",
            },
        };

        it("renders assertion, reason, and standard four relationship options", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <QuestionRenderer
                    question={arQuestion}
                    value={null}
                    onChange={onChange}
                />,
            );

            expect(
                screen.getByText("Money Bills cannot be introduced in the Rajya Sabha."),
            ).toBeInTheDocument();
            expect(
                screen.getByText(
                    "Lok Sabha is the directly elected chamber representing the people.",
                ),
            ).toBeInTheDocument();

            const radios = screen.getAllByRole("radio");
            expect(radios).toHaveLength(4);

            await user.click(radios[0]);
            expect(onChange).toHaveBeenCalledWith("BOTH_TRUE_REASON_CORRECT");
        });
    });

    describe("Match the Following Rendering", () => {
        const matchQuestion: StudentSafeQuestionData = {
            id: "v-match-1",
            question_type: "MATCH_FOLLOWING",
            text: "Match the Harappan sites with their respective river locations.",
            content: {
                left_items: [
                    { id: "l-1", text: "Harappa", position: 1 },
                    { id: "l-2", text: "Mohenjo-daro", position: 2 },
                ],
                right_items: [
                    { id: "r-1", text: "Ravi River", position: 1 },
                    { id: "r-2", text: "Indus River", position: 2 },
                ],
            },
        };

        it("renders columns and allows selecting pairwise mappings", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <QuestionRenderer
                    question={matchQuestion}
                    value={[]}
                    onChange={onChange}
                />,
            );

            expect(screen.getByText("Harappa")).toBeInTheDocument();
            expect(screen.getByText("Ravi River")).toBeInTheDocument();

            const selects = screen.getAllByRole("combobox");
            expect(selects).toHaveLength(2);

            await user.selectOptions(selects[0], "1");
            expect(onChange).toHaveBeenCalledWith([
                { left_position: 1, right_position: 1 },
            ]);
        });
    });

    describe("Descriptive Rendering", () => {
        const descQuestion: StudentSafeQuestionData = {
            id: "v-desc-1",
            question_type: "DESCRIPTIVE",
            text: "Critically evaluate the federal structure of India in light of recent fiscal developments.",
        };

        it("renders descriptive textarea and word counter without showing rubrics", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <QuestionRenderer
                    question={descQuestion}
                    value=""
                    onChange={onChange}
                />,
            );

            const textarea = screen.getByRole("textbox");
            expect(textarea).toBeInTheDocument();
            expect(screen.getByText(/0 words/i)).toBeInTheDocument();

            await user.type(textarea, "India exhibits quasi-federalism.");
            expect(onChange).toHaveBeenCalled();

            // SECURITY ASSERTIONS: No expected answer or model rubric shown
            expect(screen.queryByText(/expected answer/i)).not.toBeInTheDocument();
            expect(screen.queryByText(/rubric/i)).not.toBeInTheDocument();
        });
    });
});
