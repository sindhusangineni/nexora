import { useState, useCallback } from "react";
import { questionBankApi } from "../api/questionBankApi";
import type {
    QuestionImportExecuteResponse,
    QuestionImportPreviewResponse,
} from "../types/questionBank.types";

export type ImportStep = "upload" | "preview" | "complete";

export interface UseQuestionImportReturn {
    file: File | null;
    step: ImportStep;
    previewData: QuestionImportPreviewResponse | null;
    executeData: QuestionImportExecuteResponse | null;
    isLoadingPreview: boolean;
    isLoadingExecute: boolean;
    isDownloadingTemplate: boolean;
    error: string | null;
    skipDuplicates: boolean;
    setSkipDuplicates: (val: boolean) => void;
    selectFile: (file: File) => void;
    clearFile: () => void;
    handlePreview: () => Promise<void>;
    handleExecute: () => Promise<void>;
    handleDownloadTemplate: () => Promise<void>;
    reset: () => void;
}

export function useQuestionImport(): UseQuestionImportReturn {
    const [file, setFile] = useState<File | null>(null);
    const [step, setStep] = useState<ImportStep>("upload");
    const [previewData, setPreviewData] = useState<QuestionImportPreviewResponse | null>(null);
    const [executeData, setExecuteData] = useState<QuestionImportExecuteResponse | null>(null);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [isLoadingExecute, setIsLoadingExecute] = useState(false);
    const [isDownloadingTemplate, setIsDownloadingTemplate] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [skipDuplicates, setSkipDuplicates] = useState(true);

    const selectFile = useCallback((selectedFile: File) => {
        const name = selectedFile.name.toLowerCase();
        if (!name.endsWith(".csv") && !name.endsWith(".txt")) {
            setError("Please upload a valid CSV file (.csv).");
            return;
        }
        if (selectedFile.size > 5 * 1024 * 1024) {
            setError("File size exceeds maximum allowed limit of 5 MB.");
            return;
        }
        setError(null);
        setFile(selectedFile);
        setPreviewData(null);
        setExecuteData(null);
        setStep("upload");
    }, []);

    const clearFile = useCallback(() => {
        setFile(null);
        setError(null);
        setPreviewData(null);
        setExecuteData(null);
        setStep("upload");
    }, []);

    const handlePreview = useCallback(async () => {
        if (!file) {
            setError("Please select a CSV file first.");
            return;
        }

        setIsLoadingPreview(true);
        setError(null);

        try {
            const data = await questionBankApi.previewImport(file);
            setPreviewData(data);
            setStep("preview");
        } catch (err: unknown) {
            const apiError = err as { response?: { data?: { detail?: string; error?: string; message?: string } } };
            const msg =
                apiError.response?.data?.detail ||
                apiError.response?.data?.error ||
                apiError.response?.data?.message ||
                "Failed to parse and validate CSV file. Please check file formatting.";
            setError(msg);
        } finally {
            setIsLoadingPreview(false);
        }
    }, [file]);

    const handleExecute = useCallback(async () => {
        if (!file) {
            setError("No file available for import.");
            return;
        }
        if (previewData && !previewData.can_import) {
            setError("Cannot import: Please resolve all row errors before proceeding.");
            return;
        }

        setIsLoadingExecute(true);
        setError(null);

        try {
            const data = await questionBankApi.executeImport(file, skipDuplicates);
            setExecuteData(data);
            setStep("complete");
        } catch (err: unknown) {
            const apiError = err as { response?: { data?: { detail?: string; error?: string; message?: string } } };
            const msg =
                apiError.response?.data?.detail ||
                apiError.response?.data?.error ||
                apiError.response?.data?.message ||
                "Failed to execute import. Any changes have been rolled back.";
            setError(msg);
        } finally {
            setIsLoadingExecute(false);
        }
    }, [file, previewData, skipDuplicates]);

    const handleDownloadTemplate = useCallback(async () => {
        setIsDownloadingTemplate(true);
        setError(null);
        try {
            const blob = await questionBankApi.downloadTemplate();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "nexora_upsc_question_import_template.csv";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch {
            setError("Failed to download CSV template. Please try again.");
        } finally {
            setIsDownloadingTemplate(false);
        }
    }, []);

    const reset = useCallback(() => {
        setFile(null);
        setStep("upload");
        setPreviewData(null);
        setExecuteData(null);
        setError(null);
        setSkipDuplicates(true);
    }, []);

    return {
        file,
        step,
        previewData,
        executeData,
        isLoadingPreview,
        isLoadingExecute,
        isDownloadingTemplate,
        error,
        skipDuplicates,
        setSkipDuplicates,
        selectFile,
        clearFile,
        handlePreview,
        handleExecute,
        handleDownloadTemplate,
        reset,
    };
}
