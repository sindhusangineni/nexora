import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    CardFooter,
} from "../Card";

describe("Card Component", () => {
    it("renders card with title, description, content and footer", () => {
        render(
            <Card>
                <CardHeader>
                    <CardTitle>Card Title</CardTitle>
                    <CardDescription>Card Description</CardDescription>
                </CardHeader>
                <CardContent>
                    <p>Card Body</p>
                </CardContent>
                <CardFooter>
                    <button>Action</button>
                </CardFooter>
            </Card>,
        );

        expect(screen.getByRole("heading", { name: "Card Title" })).toBeInTheDocument();
        expect(screen.getByText("Card Description")).toBeInTheDocument();
        expect(screen.getByText("Card Body")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
    });
});
