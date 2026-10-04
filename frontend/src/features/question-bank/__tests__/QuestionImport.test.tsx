import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QuestionImportView } from "../components/QuestionImportView";
import { questionBankApi } from "../api/questionBankApi";
import type {
    QuestionImportExecuteResponse,
    QuestionImportPreviewResponse,
} from "../types/questionBank.types";

vi.mock("../api/questionBankApi", () => ({
    questionBankApi: {
        previewImport: vi.fn(),
        executeImport: vi.fn(),
        downloadTemplate: vi.fn(),
    },
}));

const mockPreviewSuccess: QuestionImportPreviewResponse = {
    total_rows: 3,
    valid_rows: 2,
    invalid_rows: 0,
    duplicate_rows: 1,
    can_import: true,
    summary: { MCQ: 2, TRUE_FALSE: 1 },
    errors: [],
    rows: [
        {
            row_number: 2,
            is_valid: true,
            is_duplicate: false,
            duplicate_reason: null,
            question_type: "MCQ",
            text: "Which Article guarantees equality before law in the Indian Constitution?",
            difficulty: "EASY",
            topic_name: "Fundamental Rights",
            topic_id: "t-1",
            source_type: "UPSC_PREVIOUS_YEAR",
            source_year: 2021,
            external_question_id: "UPSC-2021-Q1",
            errors: [],
        },
        {
            row_number: 3,
            is_valid: true,
            is_duplicate: true,
            duplicate_reason: "Question with external_question_id 'UPSC-2020-Q2' already exists in Question Bank.",
            question_type: "MCQ",
            text: "Duplicate question stem text",
            difficulty: "MEDIUM",
            topic_name: "Fundamental Rights",
            topic_id: "t-1",
            source_type: "UPSC_PREVIOUS_YEAR",
            source_year: 2020,
            external_question_id: "UPSC-2020-Q2",
            errors: [],
        },
        {
            row_number: 4,
            is_valid: true,
            is_duplicate: false,
            duplicate_reason: null,
            question_type: "TRUE_FALSE",
            text: "Preamble is an integral part of the Constitution.",
            difficulty: "EASY",
            topic_name: "Preamble",
            topic_id: "t-2",
            source_type: "ORIGINAL",
            source_year: null,
            external_question_id: null,
            errors: [],
        },
    ],
};

const mockPreviewWithErrors: QuestionImportPreviewResponse = {
    total_rows: 2,
    valid_rows: 1,
    invalid_rows: 1,
    duplicate_rows: 0,
    can_import: false,
    summary: { MCQ: 2 },
    errors: [
        {
            row_number: 3,
            field: "topic_name",
            message: 'Topic "NonExistent" was not found.',
            raw_data: { topic_name: "NonExistent" },
        },
    ],
    rows: [
        {
            row_number: 2,
            is_valid: true,
            is_duplicate: false,
            duplicate_reason: null,
            question_type: "MCQ",
            text: "Valid Question",
            difficulty: "EASY",
            topic_name: "Fundamental Rights",
            topic_id: "t-1",
            source_type: "ORIGINAL",
            source_year: null,
            external_question_id: null,
            errors: [],
        },
        {
            row_number: 3,
            is_valid: false,
            is_duplicate: false,
            duplicate_reason: null,
            question_type: "MCQ",
            text: "Invalid Question With Bad Topic",
            difficulty: "EASY",
            topic_name: "NonExistent",
            topic_id: null,
            source_type: "ORIGINAL",
            source_year: null,
            external_question_id: null,
            errors: ['Topic "NonExistent" was not found.'],
        },
    ],
};

const mockExecuteResponse: QuestionImportExecuteResponse = {
    total_rows: 3,
    imported_rows: 2,
    skipped_rows: 1,
    failed_rows: 0,
    created_question_ids: ["q-uuid-1", "q-uuid-2"],
    errors: [],
};

describe("QuestionImportView", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("renders the initial upload step with guidelines and template button", () => {
        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        expect(screen.getByText("Bulk UPSC Question Import")).toBeInTheDocument();
        expect(screen.getByText("Download CSV Template")).toBeInTheDocument();
        expect(screen.getByText("Drop your CSV file here, or click to browse")).toBeInTheDocument();
        expect(screen.getByText("All 6 Question Types")).toBeInTheDocument();
        expect(screen.getByText("Status: DRAFT Only")).toBeInTheDocument();
    });

    it("handles template download click", async () => {
        const user = userEvent.setup();
        const fakeBlob = new Blob(["question_type,text\n"], { type: "text/csv" });
        vi.mocked(questionBankApi.downloadTemplate).mockResolvedValueOnce(fakeBlob);

        // Mock window.URL.createObjectURL and revokeObjectURL
        window.URL.createObjectURL = vi.fn().mockReturnValue("blob:http://localhost/test");
        window.URL.revokeObjectURL = vi.fn();

        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const downloadBtn = screen.getByText("Download CSV Template");
        await user.click(downloadBtn);

        expect(questionBankApi.downloadTemplate).toHaveBeenCalledTimes(1);
    });

    it("rejects non-CSV files and displays an error message", async () => {
        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakePdf = new File(["dummy pdf"], "document.pdf", { type: "application/pdf" });

        fireEvent.change(input, { target: { files: [fakePdf] } });

        await waitFor(() => {
            expect(screen.getByText("Please upload a valid CSV file (.csv).")).toBeInTheDocument();
        });
    });

    it("allows selecting a valid CSV file and displays file information", async () => {
        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakeCsv = new File(["question_type,text\nMCQ,Sample question"], "questions.csv", {
            type: "text/csv",
        });

        fireEvent.change(input, { target: { files: [fakeCsv] } });

        await waitFor(() => {
            expect(screen.getByText("questions.csv")).toBeInTheDocument();
            expect(screen.getByText("Validate & Preview CSV →")).toBeInTheDocument();
        });
    });

    it("executes preview and displays KPI summary cards, question types, and row table", async () => {
        const user = userEvent.setup();
        vi.mocked(questionBankApi.previewImport).mockResolvedValueOnce(mockPreviewSuccess);

        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakeCsv = new File(["dummy"], "import.csv", { type: "text/csv" });
        fireEvent.change(input, { target: { files: [fakeCsv] } });

        const previewBtn = screen.getByText("Validate & Preview CSV →");
        await user.click(previewBtn);

        await waitFor(() => {
            expect(questionBankApi.previewImport).toHaveBeenCalledWith(fakeCsv);
            expect(screen.getByText("Validation Preview")).toBeInTheDocument();
            expect(screen.getByText("Total Rows")).toBeInTheDocument();
            expect(screen.getByText("Valid Rows")).toBeInTheDocument();
            expect(screen.getByText("Duplicate Rows")).toBeInTheDocument();
            expect(screen.getByText("Invalid Rows")).toBeInTheDocument();
            expect(screen.getByText("Which Article guarantees equality before law in the Indian Constitution?")).toBeInTheDocument();
        });
    });

    it("displays Option A blocked banner and error list when invalid rows exist", async () => {
        const user = userEvent.setup();
        vi.mocked(questionBankApi.previewImport).mockResolvedValueOnce(mockPreviewWithErrors);

        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakeCsv = new File(["dummy"], "import_with_errors.csv", { type: "text/csv" });
        fireEvent.change(input, { target: { files: [fakeCsv] } });

        const previewBtn = screen.getByText("Validate & Preview CSV →");
        await user.click(previewBtn);

        await waitFor(() => {
            expect(screen.getByText(/Import Blocked — All-or-Nothing Option A/i)).toBeInTheDocument();
            expect(screen.getByText('Topic "NonExistent" was not found.')).toBeInTheDocument();
            expect(screen.getByText(/Row 3/i)).toBeInTheDocument();
        });

        // The execute button should be disabled
        const executeBtn = screen.getByRole("button", { name: /Execute Import/i });
        expect(executeBtn).toBeDisabled();
    });

    it("executes import and renders completion summary upon success", async () => {
        const user = userEvent.setup();
        vi.mocked(questionBankApi.previewImport).mockResolvedValueOnce(mockPreviewSuccess);
        vi.mocked(questionBankApi.executeImport).mockResolvedValueOnce(mockExecuteResponse);

        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakeCsv = new File(["dummy"], "valid_import.csv", { type: "text/csv" });
        fireEvent.change(input, { target: { files: [fakeCsv] } });

        await user.click(screen.getByText("Validate & Preview CSV →"));

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /Execute Import \(2 Questions\) →/i })).toBeEnabled();
        });

        const executeBtn = screen.getByRole("button", { name: /Execute Import \(2 Questions\) →/i });
        await user.click(executeBtn);

        await waitFor(() => {
            expect(questionBankApi.executeImport).toHaveBeenCalledWith(fakeCsv, true);
            expect(screen.getByText("Bulk Import Successfully Completed")).toBeInTheDocument();
            expect(screen.getByText("Import Another CSV Batch")).toBeInTheDocument();
            expect(screen.getByText("View In Question Bank →")).toBeInTheDocument();
        });
    });

    it("allows resetting back to upload step from complete screen", async () => {
        const user = userEvent.setup();
        vi.mocked(questionBankApi.previewImport).mockResolvedValueOnce(mockPreviewSuccess);
        vi.mocked(questionBankApi.executeImport).mockResolvedValueOnce(mockExecuteResponse);

        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakeCsv = new File(["dummy"], "valid_import.csv", { type: "text/csv" });
        fireEvent.change(input, { target: { files: [fakeCsv] } });

        await user.click(screen.getByText("Validate & Preview CSV →"));
        await waitFor(() => {
            expect(screen.getByRole("button", { name: /Execute Import/i })).toBeEnabled();
        });

        await user.click(screen.getByRole("button", { name: /Execute Import/i }));
        await waitFor(() => {
            expect(screen.getByText("Import Another CSV Batch")).toBeInTheDocument();
        });

        await user.click(screen.getByText("Import Another CSV Batch"));

        expect(screen.getByText("Drop your CSV file here, or click to browse")).toBeInTheDocument();
    });

    it("displays Potential Match badge for potential textual matches", async () => {
        const user = userEvent.setup();
        const mockWithPotentialMatch: QuestionImportPreviewResponse = {
            ...mockPreviewSuccess,
            rows: [
                {
                    row_number: 2,
                    is_valid: true,
                    is_duplicate: false,
                    duplicate_type: "POTENTIAL",
                    duplicate_reason: "Potential textual similarity with an existing question in topic 'Fundamental Rights'.",
                    question_type: "MCQ",
                    text: "Potential duplicate stem text",
                    difficulty: "EASY",
                    topic_name: "Fundamental Rights",
                    topic_id: "t-1",
                    source_type: "ORIGINAL",
                    source_year: null,
                    external_question_id: null,
                    errors: [],
                },
            ],
        };
        vi.mocked(questionBankApi.previewImport).mockResolvedValueOnce(mockWithPotentialMatch);

        render(
            <MemoryRouter>
                <QuestionImportView />
            </MemoryRouter>
        );

        const input = document.querySelector('input[type="file"]') as HTMLInputElement;
        const fakeCsv = new File(["dummy"], "potential.csv", { type: "text/csv" });
        fireEvent.change(input, { target: { files: [fakeCsv] } });

        await user.click(screen.getByText("Validate & Preview CSV →"));

        await waitFor(() => {
            expect(screen.getByText("Potential Match")).toBeInTheDocument();
        });
    });
});
