import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { Modal } from "./Modal";

describe("Modal Component", () => {
    it("does not render when isOpen is false", () => {
        render(
            <Modal isOpen={false} onClose={vi.fn()} title="Test Modal">
                <div>Content</div>
            </Modal>,
        );

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("renders dialog with title and description when isOpen is true", () => {
        render(
            <Modal
                isOpen={true}
                onClose={vi.fn()}
                title="Test Modal"
                description="Modal description"
            >
                <div>Modal Content</div>
            </Modal>,
        );

        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Test Modal")).toBeInTheDocument();
        expect(screen.getByText("Modal description")).toBeInTheDocument();
        expect(screen.getByText("Modal Content")).toBeInTheDocument();
    });

    it("calls onClose when close button is clicked", () => {
        const handleClose = vi.fn();
        render(
            <Modal isOpen={true} onClose={handleClose} title="Test Modal">
                <div>Content</div>
            </Modal>,
        );

        fireEvent.click(screen.getByLabelText(/close dialog/i));
        expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it("calls onClose when Escape key is pressed", () => {
        const handleClose = vi.fn();
        render(
            <Modal isOpen={true} onClose={handleClose} title="Test Modal">
                <div>Content</div>
            </Modal>,
        );

        fireEvent.keyDown(window, { key: "Escape" });
        expect(handleClose).toHaveBeenCalledTimes(1);
    });
});
