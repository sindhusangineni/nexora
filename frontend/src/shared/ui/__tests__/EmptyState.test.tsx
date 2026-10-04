import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { EmptyState } from "../EmptyState";

describe("EmptyState Component", () => {
    it("renders title, description and action button", () => {
        render(
            <EmptyState
                title="No Data Available"
                description="Please check back later or add new items."
                action={<button>Create Item</button>}
            />,
        );

        expect(screen.getByRole("heading", { name: "No Data Available" })).toBeInTheDocument();
        expect(screen.getByText("Please check back later or add new items.")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Create Item" })).toBeInTheDocument();
    });
});
