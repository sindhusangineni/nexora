import { describe, it, expect, beforeEach, vi } from "vitest";

import {
    apiClient,
    getAccessToken,
    setAccessToken,
    setOnSessionExpired,
} from "../client";
import { ApiError, parseApiError } from "../errors";

describe("API Client & Error Handling", () => {
    beforeEach(() => {
        setAccessToken(null);
        setOnSessionExpired(null);
        vi.clearAllMocks();
    });

    describe("In-Memory Token Management", () => {
        it("stores and retrieves access token strictly in memory", () => {
            expect(getAccessToken()).toBeNull();
            setAccessToken("sample.jwt.token");
            expect(getAccessToken()).toBe("sample.jwt.token");
            setAccessToken(null);
            expect(getAccessToken()).toBeNull();
        });
    });

    describe("parseApiError", () => {
        it("correctly extracts structured Nexora backend error envelope", () => {
            const axiosError = {
                isAxiosError: true,
                response: {
                    status: 400,
                    data: {
                        error: {
                            code: "INVALID_CREDENTIALS",
                            message: "Invalid email or password.",
                            fields: {
                                email: ["Enter a valid email address."],
                            },
                        },
                    },
                },
            };

            const parsed = parseApiError(axiosError);
            expect(parsed).toBeInstanceOf(ApiError);
            expect(parsed.code).toBe("INVALID_CREDENTIALS");
            expect(parsed.message).toBe("Invalid email or password.");
            expect(parsed.status).toBe(400);
            expect(parsed.fields?.email).toContain("Enter a valid email address.");
            expect(parsed.isNetworkError).toBe(false);
        });

        it("handles network errors where no response was received", () => {
            const networkError = {
                isAxiosError: true,
                request: {},
                message: "Network Error",
            };

            const parsed = parseApiError(networkError);
            expect(parsed.code).toBe("NETWORK_ERROR");
            expect(parsed.isNetworkError).toBe(true);
        });

        it("returns existing ApiError instances without modification", () => {
            const existing = new ApiError({
                code: "CUSTOM_CODE",
                message: "Custom message",
                status: 403,
            });
            expect(parseApiError(existing)).toBe(existing);
        });
    });

    describe("Client Defaults Configuration", () => {
        it("configures withCredentials to transmit secure HttpOnly cookies", () => {
            expect(apiClient.defaults.withCredentials).toBe(true);
        });

        it("configures JSON content-type header", () => {
            expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
        });
    });
});
