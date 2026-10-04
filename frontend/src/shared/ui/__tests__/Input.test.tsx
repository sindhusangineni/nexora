import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { Input } from "../Input";

describe("Input Component", () => {
    it("renders label, placeholder and links aria attributes", () => {
        render(
            <Input
                label="Full Name"
                placeholder="Enter your name"
                helperText="First and last name"
            />,
        );

        const input = screen.getByLabelText("Full Name");
        expect(input).toBeInTheDocument();
        expect(input).toHaveAttribute("placeholder", "Enter your name");
        expect(screen.getByText("First and last name")).toBeInTheDocument();
    });

    it("displays error message and sets aria-invalid when error is present", () => {
        render(
            <Input
                label="Email"
                error="Invalid email address"
            />,
        );

        const input = screen.getByLabelText("Email");
        expect(input).toHaveAttribute("aria-invalid", "true");
        expect(screen.getByRole("alert")).toHaveTextContent("Invalid email address");
    });
});
