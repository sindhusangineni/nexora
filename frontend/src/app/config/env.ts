// Default to '/api/v1' for Vite proxy or local backend, or read from import.meta.env
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// Normalize to ensure baseURL ends with /v1
const normalizedBaseUrl = rawBaseUrl.endsWith("/v1")
    ? rawBaseUrl
    : `${rawBaseUrl.replace(/\/+$/, "")}/v1`;

export const env = {
    apiBaseUrl: normalizedBaseUrl,
} as const;