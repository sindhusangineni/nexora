import axios from "axios";

export interface BackendErrorPayload {
    error?: {
        code?: string;
        message?: string;
        fields?: Record<string, string[]>;
    };
}

export class ApiError extends Error {
    readonly code: string;
    readonly status?: number;
    readonly fields?: Record<string, string[]>;
    readonly isNetworkError: boolean;

    constructor(params: {
        code: string;
        message: string;
        status?: number;
        fields?: Record<string, string[]>;
        isNetworkError?: boolean;
    }) {
        super(params.message);
        this.name = "ApiError";
        this.code = params.code;
        this.status = params.status;
        this.fields = params.fields;
        this.isNetworkError = params.isNetworkError ?? false;

        // Ensure proper prototype chain for instanceof checks
        Object.setPrototypeOf(this, ApiError.prototype);
    }
}

export function isApiError(error: unknown): error is ApiError {
    return error instanceof ApiError;
}

export function parseApiError(error: unknown): ApiError {
    if (isApiError(error)) {
        return error;
    }

    if (axios.isAxiosError<BackendErrorPayload>(error)) {
        const status = error.response?.status;
        const data = error.response?.data;

        // Structured backend error envelope
        if (data?.error) {
            return new ApiError({
                code: data.error.code || (status ? `HTTP_${status}` : "API_ERROR"),
                message: data.error.message || "An unexpected error occurred.",
                status,
                fields: data.error.fields,
            });
        }

        // Network error (no response received)
        if (error.request && !error.response) {
            return new ApiError({
                code: "NETWORK_ERROR",
                message: "Unable to connect to the server. Please check your internet connection.",
                isNetworkError: true,
            });
        }

        // Generic HTTP error
        return new ApiError({
            code: status ? `HTTP_${status}` : "REQUEST_FAILED",
            message: error.message || "Request failed.",
            status,
        });
    }

    if (error instanceof Error) {
        return new ApiError({
            code: "UNKNOWN_ERROR",
            message: error.message,
        });
    }

    return new ApiError({
        code: "UNKNOWN_ERROR",
        message: "An unknown error occurred.",
    });
}
