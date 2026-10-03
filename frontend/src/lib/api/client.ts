import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { env } from "@/app/config/env";
import { parseApiError } from "./errors";

// In-memory access token storage (never persisted to localStorage/sessionStorage)
let inMemoryAccessToken: string | null = null;
let onSessionExpiredCallback: (() => void) | null = null;

export function getAccessToken(): string | null {
    return inMemoryAccessToken;
}

export function setAccessToken(token: string | null): void {
    inMemoryAccessToken = token;
}

export function setOnSessionExpired(callback: (() => void) | null): void {
    onSessionExpiredCallback = callback;
}

// Concurrency control for token refresh
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown | null, token: string | null = null) {
    failedQueue.forEach((promise) => {
        if (error) {
            promise.reject(error);
        } else if (token) {
            promise.resolve(token);
        }
    });
    failedQueue = [];
}

export const apiClient: AxiosInstance = axios.create({
    baseURL: env.apiBaseUrl,
    withCredentials: true, // Transmit HttpOnly refresh_token cookie
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor: Attach in-memory access token
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        if (inMemoryAccessToken && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
        }
        return config;
    },
    (error) => Promise.reject(parseApiError(error)),
);

// Response interceptor: Handle 401 with concurrency-protected refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

        if (!originalRequest) {
            return Promise.reject(parseApiError(error));
        }

        const isAuthUrl =
            originalRequest.url?.includes("/auth/login") ||
            originalRequest.url?.includes("/auth/refresh") ||
            originalRequest.url?.includes("/auth/logout");

        // Do not attempt token refresh for auth endpoints or if already retried
        if (error.response?.status !== 401 || isAuthUrl || originalRequest._retry) {
            return Promise.reject(parseApiError(error));
        }

        // If a refresh is already in-flight, queue this request
        if (isRefreshing) {
            return new Promise<string>((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then((newToken) => {
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return apiClient.request(originalRequest);
                })
                .catch((queueError) => Promise.reject(parseApiError(queueError)));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            // Call refresh endpoint using HttpOnly cookie
            const response = await axios.post<{ access: string }>(
                `${env.apiBaseUrl}/auth/refresh/`,
                {},
                { withCredentials: true },
            );

            const newAccessToken = response.data.access;
            setAccessToken(newAccessToken);

            processQueue(null, newAccessToken);

            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient.request(originalRequest);
        } catch (refreshError) {
            setAccessToken(null);
            processQueue(refreshError, null);

            if (onSessionExpiredCallback) {
                onSessionExpiredCallback();
            }

            return Promise.reject(parseApiError(refreshError));
        } finally {
            isRefreshing = false;
        }
    },
);
