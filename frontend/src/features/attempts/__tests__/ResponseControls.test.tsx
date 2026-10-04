import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { McqResponse } from "../components/ResponseControls/McqResponse";
import { MultipleSelectResponse } from "../components/ResponseControls/MultipleSelectResponse";
import { TrueFalseResponse } from "../components/ResponseControls/TrueFalseResponse";
import { AssertionReasonResponse } from "../components/ResponseControls/AssertionReasonResponse";
import { MatchFollowingResponse } from "../components/ResponseControls/MatchFollowingResponse";
import { DescriptiveResponse } from "../components/ResponseControls/DescriptiveResponse";

describe("Response Controls", () => {
    describe("McqResponse", () => {
        const choices = [
            { id: "c1", text: "Paris", position: 1 },
            { id: "c2", text: "Berlin", position: 2 },
        ];

        it("renders choices and selects an option", () => {
            const handleChange = vi.fn();
            render(
                <McqResponse
                    choices={choices}
                    selectedChoiceId={null}
                    onChange={handleChange}
                />,
            );

            expect(screen.getByText("Paris")).toBeInTheDocument();
            expect(screen.getByText("Berlin")).toBeInTheDocument();

            fireEvent.click(screen.getByText("Paris"));
            expect(handleChange).toHaveBeenCalledWith("c1");
        });
    });

    describe("MultipleSelectResponse", () => {
        const choices = [
            { id: "c1", text: "Fundamental Rights", position: 1 },
            { id: "c2", text: "DPSP", position: 2 },
            { id: "c3", text: "Fundamental Duties", position: 3 },
        ];

        it("allows toggling multiple choices", () => {
            const handleChange = vi.fn();
            const { rerender } = render(
                <MultipleSelectResponse
                    choices={choices}
                    selectedChoiceIds={["c1"]}
                    onChange={handleChange}
                />,
            );

            fireEvent.click(screen.getByText("DPSP"));
            expect(handleChange).toHaveBeenCalledWith(["c1", "c2"]);

            // Toggling already selected removes it
            rerender(
                <MultipleSelectResponse
                    choices={choices}
                    selectedChoiceIds={["c1", "c2"]}
                    onChange={handleChange}
                />,
            );

            fireEvent.click(screen.getByText("Fundamental Rights"));
            expect(handleChange).toHaveBeenCalledWith(["c2"]);
        });
    });

    describe("TrueFalseResponse", () => {
        it("renders True and False buttons and fires change", () => {
            const handleChange = vi.fn();
            render(
                <TrueFalseResponse
                    value={null}
                    onChange={handleChange}
                />,
            );

            const trueBtn = screen.getByRole("button", { name: "True" });
            const falseBtn = screen.getByRole("button", { name: "False" });

            expect(trueBtn).toBeInTheDocument();
            expect(falseBtn).toBeInTheDocument();

            fireEvent.click(trueBtn);
            expect(handleChange).toHaveBeenCalledWith(true);

            fireEvent.click(falseBtn);
            expect(handleChange).toHaveBeenCalledWith(false);
        });
    });

    describe("AssertionReasonResponse", () => {
        it("renders assertion and reason and handles selection", () => {
            const handleChange = vi.fn();
            render(
                <AssertionReasonResponse
                    assertion="The President is the head of state."
                    reason="India is a parliamentary republic."
                    value={null}
                    onChange={handleChange}
                />,
            );

            expect(screen.getByText(/The President is the head of state/i)).toBeInTheDocument();
            expect(screen.getByText(/India is a parliamentary republic/i)).toBeInTheDocument();

            const option1 = screen.getByText(/Both Assertion \(A\) and Reason \(R\) are true, and Reason is the correct explanation/i);
            expect(option1).toBeInTheDocument();

            fireEvent.click(option1);
            expect(handleChange).toHaveBeenCalledWith("BOTH_TRUE_REASON_CORRECT");
        });
    });

    describe("MatchFollowingResponse", () => {
        const leftItems = [
            { id: "l1", text: "Article 14", position: 1 },
            { id: "l2", text: "Article 21", position: 2 },
        ];
        const rightItems = [
            { id: "r1", text: "Right to Equality", position: 1 },
            { id: "r2", text: "Right to Life", position: 2 },
        ];

        it("renders left items and selects matches", () => {
            const handleChange = vi.fn();
            render(
                <MatchFollowingResponse
                    leftItems={leftItems}
                    rightItems={rightItems}
                    selectedMatches={[]}
                    onChange={handleChange}
                />,
            );

            expect(screen.getByText("Article 14")).toBeInTheDocument();
            expect(screen.getByText("Article 21")).toBeInTheDocument();

            const select = screen.getByLabelText(/Match for Article 14/i);
            fireEvent.change(select, { target: { value: "r1" } });

            expect(handleChange).toHaveBeenCalledWith([
                { left_item_id: "l1", right_item_id: "r1" },
            ]);
        });
    });

    describe("DescriptiveResponse", () => {
        it("renders textarea, computes word count, and handles input", () => {
            const handleChange = vi.fn();
            render(
                <DescriptiveResponse
                    value="The basic structure doctrine preserves constitutional identity."
                    onChange={handleChange}
                />,
            );

            const textarea = screen.getByPlaceholderText(/Type your comprehensive written answer here/i);
            expect(textarea).toBeInTheDocument();
            expect(screen.getByText(/7 words/i)).toBeInTheDocument();

            fireEvent.change(textarea, { target: { value: "New updated text response." } });
            expect(handleChange).toHaveBeenCalledWith("New updated text response.");
        });
    });
});
