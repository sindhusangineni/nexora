import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { McqEditor } from "../components/editors/McqEditor";
import { MultipleSelectEditor } from "../components/editors/MultipleSelectEditor";
import { TrueFalseEditor } from "../components/editors/TrueFalseEditor";
import { AssertionReasonEditor } from "../components/editors/AssertionReasonEditor";
import { MatchFollowingEditor } from "../components/editors/MatchFollowingEditor";
import { DescriptiveEditor } from "../components/editors/DescriptiveEditor";

describe("Question Type Editors", () => {
    describe("McqEditor", () => {
        it("renders initial choices and allows selecting a single correct answer", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            const choices = [
                { text: "Paris", is_correct: false, position: 1 },
                { text: "London", is_correct: true, position: 2 },
            ];

            render(<McqEditor choices={choices} onChange={onChange} />);

            expect(screen.getByDisplayValue("Paris")).toBeInTheDocument();
            expect(screen.getByDisplayValue("London")).toBeInTheDocument();

            // Select Paris as correct
            const radios = screen.getAllByRole("radio");
            expect(radios).toHaveLength(2);
            expect(radios[1]).toBeChecked();

            await user.click(radios[0]);
            expect(onChange).toHaveBeenCalledWith([
                { text: "Paris", is_correct: true, position: 1 },
                { text: "London", is_correct: false, position: 2 },
            ]);
        });

        it("allows adding and removing choices with minimum 2 enforcement", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            const choices = [
                { text: "Choice 1", is_correct: true, position: 1 },
                { text: "Choice 2", is_correct: false, position: 2 },
            ];

            const { rerender } = render(<McqEditor choices={choices} onChange={onChange} />);

            // When only 2 choices, delete button is hidden to enforce min 2
            expect(screen.queryByTitle(/remove option/i)).not.toBeInTheDocument();

            // Add Option button
            const addButton = screen.getByRole("button", { name: /\+ add option/i });
            await user.click(addButton);

            expect(onChange).toHaveBeenCalledWith([
                { text: "Choice 1", is_correct: true, position: 1 },
                { text: "Choice 2", is_correct: false, position: 2 },
                { text: "", is_correct: false, position: 3 },
            ]);

            // When 3 choices are passed, delete buttons are rendered
            rerender(
                <McqEditor
                    choices={[
                        ...choices,
                        { text: "Choice 3", is_correct: false, position: 3 },
                    ]}
                    onChange={onChange}
                />,
            );
            expect(screen.getAllByTitle(/remove option/i)).toHaveLength(3);
        });
    });

    describe("MultipleSelectEditor", () => {
        it("allows selecting multiple correct answers using checkboxes", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            const choices = [
                { text: "Statement 1", is_correct: true, position: 1 },
                { text: "Statement 2", is_correct: false, position: 2 },
                { text: "Statement 3", is_correct: false, position: 3 },
            ];

            render(<MultipleSelectEditor choices={choices} onChange={onChange} />);

            const checkboxes = screen.getAllByRole("checkbox");
            expect(checkboxes).toHaveLength(3);
            expect(checkboxes[0]).toBeChecked();
            expect(checkboxes[1]).not.toBeChecked();

            // Check statement 2 as well
            await user.click(checkboxes[1]);

            expect(onChange).toHaveBeenCalledWith([
                { text: "Statement 1", is_correct: true, position: 1 },
                { text: "Statement 2", is_correct: true, position: 2 },
                { text: "Statement 3", is_correct: false, position: 3 },
            ]);
        });
    });

    describe("TrueFalseEditor", () => {
        it("renders True and False buttons and toggles correct selection", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(<TrueFalseEditor answer={true} onChange={onChange} />);

            const trueBtn = screen.getByRole("button", { name: /true/i });
            const falseBtn = screen.getByRole("button", { name: /false/i });

            expect(trueBtn).toBeInTheDocument();
            expect(falseBtn).toBeInTheDocument();

            await user.click(falseBtn);
            expect(onChange).toHaveBeenCalledWith(false);
        });
    });

    describe("AssertionReasonEditor", () => {
        it("allows editing assertion, reason, and choosing correct relationship", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(
                <AssertionReasonEditor
                    assertion="Fundamental Rights are justiciable."
                    reason="They can be enforced directly through courts."
                    relationship="BOTH_TRUE_REASON_CORRECT"
                    onChange={onChange}
                />,
            );

            expect(
                screen.getByDisplayValue("Fundamental Rights are justiciable."),
            ).toBeInTheDocument();
            expect(
                screen.getByDisplayValue(
                    "They can be enforced directly through courts.",
                ),
            ).toBeInTheDocument();

            const select = screen.getByRole("combobox");
            expect(select).toHaveValue("BOTH_TRUE_REASON_CORRECT");

            await user.selectOptions(select, "ASSERTION_TRUE_REASON_FALSE");
            expect(onChange).toHaveBeenCalledWith({
                assertion: "Fundamental Rights are justiciable.",
                reason: "They can be enforced directly through courts.",
                relationship: "ASSERTION_TRUE_REASON_FALSE",
            });
        });
    });

    describe("MatchFollowingEditor", () => {
        it("renders pairs and allows updating left/right items and mappings", async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            const leftItems = [
                { text: "Harappa", position: 1 },
                { text: "Mohenjo-daro", position: 2 },
            ];
            const rightItems = [
                { text: "Ravi River", position: 1 },
                { text: "Indus River", position: 2 },
            ];
            const pairs = [
                { left_position: 1, right_position: 1 },
                { left_position: 2, right_position: 2 },
            ];

            render(
                <MatchFollowingEditor
                    leftItems={leftItems}
                    rightItems={rightItems}
                    pairs={pairs}
                    onChange={onChange}
                />,
            );

            expect(screen.getByDisplayValue("Harappa")).toBeInTheDocument();
            expect(screen.getByDisplayValue("Indus River")).toBeInTheDocument();

            // Check pair selects
            const comboboxes = screen.getAllByRole("combobox");
            expect(comboboxes.length).toBeGreaterThanOrEqual(2);

            // Change mapping for item 1
            await user.selectOptions(comboboxes[0], "2");
            expect(onChange).toHaveBeenCalledWith({
                leftItems,
                rightItems,
                pairs: [
                    { left_position: 1, right_position: 2 },
                    { left_position: 2, right_position: 2 },
                ],
            });
        });
    });

    describe("DescriptiveEditor", () => {
        it("renders marks input and expected answer rubric textarea", () => {
            const onChange = vi.fn();

            render(
                <DescriptiveEditor
                    marks={15}
                    expectedAnswer="Evaluate the impact of climate change on monsoon patterns."
                    onChange={onChange}
                />,
            );

            const marksInput = screen.getByRole("spinbutton");
            expect(marksInput).toHaveValue(15);

            const rubricTextarea = screen.getByRole("textbox");
            expect(rubricTextarea).toHaveValue(
                "Evaluate the impact of climate change on monsoon patterns.",
            );

            fireEvent.change(marksInput, { target: { value: "20" } });
            expect(onChange).toHaveBeenCalledWith({
                marks: 20,
                expectedAnswer: "Evaluate the impact of climate change on monsoon patterns.",
            });
        });
    });
});
