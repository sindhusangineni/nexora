import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { useQuestionImport } from "../hooks/useQuestionImport";

export function QuestionImportView() {
    const {
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
    } = useQuestionImport();

    const fileInputRef = useRef<HTMLInputElement>(null);
    const [previewFilter, setPreviewFilter] = useState<"all" | "valid" | "duplicate" | "invalid">("all");
    const [dragOver, setDragOver] = useState(false);

    const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            selectFile(e.target.files[0]);
        }
    };

    const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setDragOver(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            selectFile(e.dataTransfer.files[0]);
        }
    };

    const filteredPreviewRows = previewData?.rows.filter((r) => {
        if (previewFilter === "valid") return r.is_valid && !r.is_duplicate;
        if (previewFilter === "duplicate") return r.is_duplicate;
        if (previewFilter === "invalid") return !r.is_valid;
        return true;
    }) ?? [];

    return (
        <div className="space-y-6 max-w-6xl mx-auto">
            {/* Header & Breadcrumb */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Link
                            to="/admin/question-bank"
                            className="text-xs text-foreground-muted hover:text-foreground transition-colors"
                        >
                            Question Bank
                        </Link>
                        <span className="text-xs text-foreground-muted">/</span>
                        <Badge variant="default" size="sm">
                            Phase 3F
                        </Badge>
                        <span className="text-xs text-foreground-muted">Bulk Ingestion</span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        Bulk UPSC Question Import
                    </h1>
                    <p className="text-sm text-foreground-muted mt-1">
                        Upload, validate, preview, and ingest UPSC questions in bulk with deterministic taxonomy resolution.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <Button
                        type="button"
                        variant="secondary"
                        size="md"
                        onClick={handleDownloadTemplate}
                        disabled={isDownloadingTemplate}
                    >
                        {isDownloadingTemplate ? "Downloading..." : "Download CSV Template"}
                    </Button>
                    <Link to="/admin/question-bank">
                        <Button variant="ghost" size="md">
                            Back to Bank
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Step Progress Tracker */}
            <div className="grid grid-cols-3 gap-2 py-2">
                <div
                    className={`flex items-center gap-2.5 p-3 rounded-lg border text-sm font-medium transition-colors ${
                        step === "upload"
                            ? "border-neutral-900 bg-neutral-900 text-white shadow-xs"
                            : "border-border bg-card text-foreground-muted"
                    }`}
                >
                    <span className="w-6 h-6 flex items-center justify-center rounded-full bg-neutral-700 text-white text-xs font-bold">
                        1
                    </span>
                    <span>Upload CSV</span>
                </div>

                <div
                    className={`flex items-center gap-2.5 p-3 rounded-lg border text-sm font-medium transition-colors ${
                        step === "preview"
                            ? "border-neutral-900 bg-neutral-900 text-white shadow-xs"
                            : "border-border bg-card text-foreground-muted"
                    }`}
                >
                    <span className="w-6 h-6 flex items-center justify-center rounded-full bg-neutral-700 text-white text-xs font-bold">
                        2
                    </span>
                    <span>Validation Preview</span>
                </div>

                <div
                    className={`flex items-center gap-2.5 p-3 rounded-lg border text-sm font-medium transition-colors ${
                        step === "complete"
                            ? "border-emerald-600 bg-emerald-600 text-white shadow-xs"
                            : "border-border bg-card text-foreground-muted"
                    }`}
                >
                    <span className="w-6 h-6 flex items-center justify-center rounded-full bg-neutral-700 text-white text-xs font-bold">
                        3
                    </span>
                    <span>Import Complete</span>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div
                    role="alert"
                    className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-900 text-sm flex items-start gap-3"
                >
                    <span className="font-bold text-red-600">Error:</span>
                    <div className="flex-1">{error}</div>
                </div>
            )}

            {/* STEP 1: Upload State */}
            {step === "upload" && (
                <div className="space-y-6">
                    {/* Information Guidelines Box */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base font-semibold">
                                Import Rules & Specifications
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm text-foreground-muted">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="p-3.5 rounded-lg bg-neutral-50 border border-neutral-200/60">
                                    <h4 className="font-semibold text-foreground text-xs uppercase tracking-wide mb-1">
                                        All 6 Question Types
                                    </h4>
                                    <p className="text-xs">
                                        Supports MCQ, MULTIPLE_SELECT, TRUE_FALSE, ASSERTION_REASON, MATCH_FOLLOWING, and DESCRIPTIVE.
                                    </p>
                                </div>
                                <div className="p-3.5 rounded-lg bg-neutral-50 border border-neutral-200/60">
                                    <h4 className="font-semibold text-foreground text-xs uppercase tracking-wide mb-1">
                                        Status: DRAFT Only
                                    </h4>
                                    <p className="text-xs">
                                        All ingested questions enter as Version 1 in DRAFT status. No question bypasses editorial review.
                                    </p>
                                </div>
                                <div className="p-3.5 rounded-lg bg-neutral-50 border border-neutral-200/60">
                                    <h4 className="font-semibold text-foreground text-xs uppercase tracking-wide mb-1">
                                        Atomic Option A
                                    </h4>
                                    <p className="text-xs">
                                        All-or-Nothing execution ensures batches with any invalid rows are completely rejected to prevent partial state corruption.
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Dropzone Card */}
                    <Card>
                        <CardContent className="p-8">
                            <div
                                onDragOver={(e) => {
                                    e.preventDefault();
                                    setDragOver(true);
                                }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={onDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                                    dragOver
                                        ? "border-neutral-900 bg-neutral-50"
                                        : file
                                        ? "border-emerald-500 bg-emerald-50/20"
                                        : "border-border hover:border-neutral-400 bg-card"
                                }`}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".csv,text/csv"
                                    onChange={onFileChange}
                                    className="hidden"
                                />

                                <div className="space-y-3">
                                    <div className="w-12 h-12 mx-auto rounded-full bg-neutral-100 flex items-center justify-center text-foreground">
                                        <svg
                                            className="w-6 h-6"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth={2}
                                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                            />
                                        </svg>
                                    </div>

                                    {file ? (
                                        <div>
                                            <p className="text-base font-semibold text-foreground">
                                                {file.name}
                                            </p>
                                            <p className="text-xs text-foreground-muted mt-1">
                                                {(file.size / 1024).toFixed(1)} KB — Ready to parse
                                            </p>
                                        </div>
                                    ) : (
                                        <div>
                                            <p className="text-base font-semibold text-foreground">
                                                Drop your CSV file here, or click to browse
                                            </p>
                                            <p className="text-xs text-foreground-muted mt-1">
                                                Up to 500 rows per batch, maximum 5 MB (UTF-8 encoding)
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {file && (
                                <div className="mt-6 flex items-center justify-between pt-4 border-t border-border">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            clearFile();
                                        }}
                                    >
                                        Remove File
                                    </Button>

                                    <Button
                                        type="button"
                                        variant="primary"
                                        size="md"
                                        onClick={handlePreview}
                                        disabled={isLoadingPreview}
                                    >
                                        {isLoadingPreview ? "Parsing & Validating..." : "Validate & Preview CSV →"}
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* STEP 2: Preview & Validation Results */}
            {step === "preview" && previewData && (
                <div className="space-y-6">
                    {/* Summary KPI Cards */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-4">
                                <span className="text-xs font-medium text-foreground-muted uppercase tracking-wider">
                                    Total Rows
                                </span>
                                <p className="text-2xl font-bold text-foreground mt-1">
                                    {previewData.total_rows}
                                </p>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="p-4">
                                <span className="text-xs font-medium text-emerald-600 uppercase tracking-wider">
                                    Valid Rows
                                </span>
                                <p className="text-2xl font-bold text-emerald-600 mt-1">
                                    {previewData.valid_rows}
                                </p>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="p-4">
                                <span className="text-xs font-medium text-amber-600 uppercase tracking-wider">
                                    Duplicate Rows
                                </span>
                                <p className="text-2xl font-bold text-amber-600 mt-1">
                                    {previewData.duplicate_rows}
                                </p>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="p-4">
                                <span className="text-xs font-medium text-red-600 uppercase tracking-wider">
                                    Invalid Rows
                                </span>
                                <p className="text-2xl font-bold text-red-600 mt-1">
                                    {previewData.invalid_rows}
                                </p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Question Type Breakdown */}
                    {Object.keys(previewData.summary).length > 0 && (
                        <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-medium text-foreground-muted mr-1">
                                Question Types:
                            </span>
                            {Object.entries(previewData.summary).map(([qType, count]) => (
                                <Badge key={qType} variant="default" size="sm">
                                    {qType}: <span className="font-bold ml-1">{count}</span>
                                </Badge>
                            ))}
                        </div>
                    )}

                    {/* Option A Warning if Invalid Rows exist */}
                    {!previewData.can_import && (
                        <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-950 space-y-2">
                            <div className="flex items-center gap-2 font-bold text-red-800">
                                <span>⚠️ Import Blocked — All-or-Nothing Option A</span>
                            </div>
                            <p className="text-sm text-red-900">
                                This import batch contains {previewData.invalid_rows} row-level error(s).
                                Under Nexora transaction safety policies, no questions can be imported until all errors in the CSV are corrected.
                            </p>
                        </div>
                    )}

                    {/* Validation Errors Table if any */}
                    {previewData.errors.length > 0 && (
                        <Card>
                            <CardHeader className="border-b border-border bg-neutral-50/50">
                                <CardTitle className="text-sm font-semibold text-red-700 flex items-center justify-between">
                                    <span>Validation Errors ({previewData.errors.length})</span>
                                    <span className="text-xs font-normal text-foreground-muted">
                                        Check CSV row numbers below
                                    </span>
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-0 max-h-72 overflow-y-auto">
                                <table className="w-full text-left text-xs">
                                    <thead className="bg-neutral-100 text-foreground-muted sticky top-0">
                                        <tr>
                                            <th className="py-2.5 px-4 font-semibold w-24">Row</th>
                                            <th className="py-2.5 px-4 font-semibold w-40">Field</th>
                                            <th className="py-2.5 px-4 font-semibold">Error Message</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border">
                                        {previewData.errors.map((err, idx) => (
                                            <tr key={idx} className="hover:bg-neutral-50/60">
                                                <td className="py-2.5 px-4 font-mono font-bold text-red-600">
                                                    Row {err.row_number}
                                                </td>
                                                <td className="py-2.5 px-4 font-mono text-neutral-800">
                                                    {err.field}
                                                </td>
                                                <td className="py-2.5 px-4 text-foreground">
                                                    {err.message}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </CardContent>
                        </Card>
                    )}

                    {/* Rows Preview Table */}
                    <Card>
                        <CardHeader className="border-b border-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <CardTitle className="text-base font-semibold">
                                Batch Rows Preview
                            </CardTitle>

                            {/* Row Status Filter Buttons */}
                            <div className="flex items-center gap-1">
                                {(["all", "valid", "duplicate", "invalid"] as const).map((filterKey) => (
                                    <button
                                        key={filterKey}
                                        type="button"
                                        onClick={() => setPreviewFilter(filterKey)}
                                        className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                                            previewFilter === filterKey
                                                ? "bg-neutral-900 text-white"
                                                : "text-foreground-muted hover:text-foreground hover:bg-neutral-100"
                                        }`}
                                    >
                                        {filterKey.charAt(0).toUpperCase() + filterKey.slice(1)}
                                    </button>
                                ))}
                            </div>
                        </CardHeader>
                        <CardContent className="p-0 overflow-x-auto">
                            <table className="w-full text-left text-xs min-w-[700px]">
                                <thead className="bg-neutral-50 text-foreground-muted border-b border-border">
                                    <tr>
                                        <th className="py-2.5 px-3 font-semibold w-14">#</th>
                                        <th className="py-2.5 px-3 font-semibold w-24">Status</th>
                                        <th className="py-2.5 px-3 font-semibold w-28">Type</th>
                                        <th className="py-2.5 px-3 font-semibold">Question Stem</th>
                                        <th className="py-2.5 px-3 font-semibold w-24">Difficulty</th>
                                        <th className="py-2.5 px-3 font-semibold w-36">Topic</th>
                                        <th className="py-2.5 px-3 font-semibold w-28">Source</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {filteredPreviewRows.length === 0 ? (
                                        <tr>
                                            <td colSpan={7} className="py-8 text-center text-foreground-muted">
                                                No rows match the selected filter.
                                            </td>
                                        </tr>
                                    ) : (
                                        filteredPreviewRows.map((r) => (
                                            <tr key={r.row_number} className="hover:bg-neutral-50/60">
                                                <td className="py-2.5 px-3 font-mono text-foreground-muted">
                                                    {r.row_number}
                                                </td>
                                                <td className="py-2.5 px-3">
                                                    {!r.is_valid ? (
                                                        <Badge variant="danger" size="sm">
                                                            Invalid
                                                        </Badge>
                                                    ) : r.is_duplicate ? (
                                                        <Badge variant="warning" size="sm" title={r.duplicate_reason || undefined}>
                                                            Duplicate
                                                        </Badge>
                                                    ) : r.duplicate_type === "POTENTIAL" ? (
                                                        <Badge variant="warning" size="sm" title={r.duplicate_reason || undefined}>
                                                            Potential Match
                                                        </Badge>
                                                    ) : (
                                                        <Badge variant="success" size="sm">
                                                            Valid
                                                        </Badge>
                                                    )}
                                                </td>
                                                <td className="py-2.5 px-3 font-mono font-semibold">
                                                    {r.question_type || "—"}
                                                </td>
                                                <td className="py-2.5 px-3 font-medium text-foreground max-w-xs truncate">
                                                    {r.text}
                                                </td>
                                                <td className="py-2.5 px-3 text-foreground-muted">
                                                    {r.difficulty || "—"}
                                                </td>
                                                <td className="py-2.5 px-3 text-foreground-muted truncate max-w-[140px]">
                                                    {r.topic_name || "—"}
                                                </td>
                                                <td className="py-2.5 px-3 text-foreground-muted truncate">
                                                    {r.source_type ? `${r.source_type} ${r.source_year || ""}` : "—"}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>

                    {/* Bottom Action Bar */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl border border-border bg-card">
                        <div className="flex items-center gap-3">
                            <label className="flex items-center gap-2 cursor-pointer text-sm text-foreground select-none">
                                <input
                                    type="checkbox"
                                    checked={skipDuplicates}
                                    onChange={(e) => setSkipDuplicates(e.target.checked)}
                                    className="rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900"
                                />
                                <span>Skip existing duplicates (recommended)</span>
                            </label>
                        </div>

                        <div className="flex items-center gap-3">
                            <Button
                                type="button"
                                variant="secondary"
                                size="md"
                                onClick={clearFile}
                            >
                                Choose Different File
                            </Button>

                            <Button
                                type="button"
                                variant="primary"
                                size="md"
                                onClick={handleExecute}
                                disabled={!previewData.can_import || isLoadingExecute}
                            >
                                {isLoadingExecute
                                    ? "Executing Import..."
                                    : `Execute Import (${previewData.valid_rows} Questions) →`}
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* STEP 3: Complete State */}
            {step === "complete" && executeData && (
                <div className="space-y-6">
                    <Card className="border-emerald-200 bg-emerald-50/30">
                        <CardContent className="p-8 text-center space-y-4">
                            <div className="w-16 h-16 mx-auto rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                                <svg
                                    className="w-8 h-8"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M5 13l4 4L19 7"
                                    />
                                </svg>
                            </div>

                            <h2 className="text-2xl font-bold text-foreground">
                                Bulk Import Successfully Completed
                            </h2>
                            <p className="text-sm text-foreground-muted max-w-lg mx-auto">
                                All valid questions have been ingested as <span className="font-semibold text-foreground">DRAFT</span> (Version 1).
                                They are immediately available for editorial review and approval in the Question Bank.
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-md mx-auto pt-4">
                                <div className="p-3 bg-white rounded-lg border border-neutral-200">
                                    <span className="text-xs text-foreground-muted uppercase">Imported</span>
                                    <p className="text-xl font-bold text-emerald-600">
                                        {executeData.imported_rows}
                                    </p>
                                </div>
                                <div className="p-3 bg-white rounded-lg border border-neutral-200">
                                    <span className="text-xs text-foreground-muted uppercase">Skipped</span>
                                    <p className="text-xl font-bold text-amber-600">
                                        {executeData.skipped_rows}
                                    </p>
                                </div>
                                <div className="p-3 bg-white rounded-lg border border-neutral-200">
                                    <span className="text-xs text-foreground-muted uppercase">Total Rows</span>
                                    <p className="text-xl font-bold text-foreground">
                                        {executeData.total_rows}
                                    </p>
                                </div>
                            </div>

                            <div className="pt-6 flex flex-wrap items-center justify-center gap-4">
                                <Button
                                    type="button"
                                    variant="secondary"
                                    size="md"
                                    onClick={reset}
                                >
                                    Import Another CSV Batch
                                </Button>
                                <Link to="/admin/question-bank">
                                    <Button variant="primary" size="md">
                                        View In Question Bank →
                                    </Button>
                                </Link>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
