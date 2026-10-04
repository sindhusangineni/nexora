import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { Badge } from "../Badge";

describe("Badge Component", () => {
    it("renders children text", () => {
        render(<Badge>Test Badge</Badge>);
        expect(screen.getByText("Test Badge")).toBeInTheDocument();
    });

    it("applies variant classes correctly", () => {
        const { rerender } = render(<Badge variant="success">Success</Badge>);
        expect(screen.getByText("Success")).toHaveClass("bg-emerald-50");

        rerender(<Badge variant="danger">Danger</Badge>);
        expect(screen.getByText("Danger")).toHaveClass("bg-red-50");

        rerender(<Badge variant="primary">Primary</Badge>);
        expect(screen.getByText("Primary")).toHaveClass("bg-primary-50");
    });
});
