import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "./Button";

describe("Button", () => {
    it("renders its label", () => {
        render(<Button>Continue</Button>);

        expect(
            screen.getByRole("button", { name: "Continue" }),
        ).toBeInTheDocument();
    });

    it("supports button variants", () => {
        render(<Button variant="secondary">Cancel</Button>);

        expect(
            screen.getByRole("button", { name: "Cancel" }),
        ).toHaveAttribute("data-variant", "secondary");
    });

    it("supports button sizes", () => {
        render(<Button size="lg">Create account</Button>);

        expect(
            screen.getByRole("button", { name: "Create account" }),
        ).toHaveAttribute("data-size", "lg");
    });

    it("can be disabled", () => {
        render(<Button disabled>Submit</Button>);

        expect(
            screen.getByRole("button", { name: "Submit" }),
        ).toBeDisabled();
    });

    it("shows loading state", () => {
        render(<Button loading>Submit</Button>);

        const button = screen.getByRole("button", { name: "Submit" });

        expect(button).toBeDisabled();
        expect(button).toHaveAttribute("aria-busy", "true");
    });

    it("supports native button type", () => {
        render(<Button type="submit">Submit</Button>);

        expect(
            screen.getByRole("button", { name: "Submit" }),
        ).toHaveAttribute("type", "submit");
    });

    it("merges custom className without dropping styles", () => {
        render(<Button className="custom-class">Custom</Button>);

        expect(
            screen.getByRole("button", { name: "Custom" }),
        ).toHaveClass("custom-class");
    });

    it("supports danger and ghost variants", () => {
        const { rerender } = render(<Button variant="danger">Delete</Button>);
        expect(
            screen.getByRole("button", { name: "Delete" }),
        ).toHaveAttribute("data-variant", "danger");

        rerender(<Button variant="ghost">Dismiss</Button>);
        expect(
            screen.getByRole("button", { name: "Dismiss" }),
        ).toHaveAttribute("data-variant", "ghost");
    });

    it("supports sm and md sizes", () => {
        const { rerender } = render(<Button size="sm">Small</Button>);
        expect(
            screen.getByRole("button", { name: "Small" }),
        ).toHaveAttribute("data-size", "sm");

        rerender(<Button size="md">Medium</Button>);
        expect(
            screen.getByRole("button", { name: "Medium" }),
        ).toHaveAttribute("data-size", "md");
    });
});
