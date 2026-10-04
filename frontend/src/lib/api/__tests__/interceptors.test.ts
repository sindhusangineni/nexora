import { describe, it, expect, beforeEach, vi } from "vitest";
import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from "axios";

import {
    apiClient,
    getAccessToken,
    setAccessToken,
    setOnSessionExpired,
} from "../client";
import { ApiError } from "../errors";

describe("API Client Interceptor Logic", () => {
    beforeEach(() => {
        setAccessToken(null);
        setOnSessionExpired(null);
        vi.restoreAllMocks();
    });

    it("attaches Authorization header when in-memory access token is set", async () => {
        setAccessToken("test.jwt.token");

        // @ts-expect-error accessing internal interceptor handlers for testing
        const requestInterceptor = apiClient.interceptors.request.handlers[0];

        const config = {
            headers: {} as Record<string, string>,
        } as InternalAxiosRequestConfig;

        const updatedConfig = await requestInterceptor.fulfilled(config);
        expect(updatedConfig.headers.Authorization).toBe("Bearer test.jwt.token");
    });

    it("does not attach Authorization header when no access token exists", async () => {
        setAccessToken(null);

        // @ts-expect-error accessing internal interceptor handlers for testing
        const requestInterceptor = apiClient.interceptors.request.handlers[0];

        const config = {
            headers: {} as Record<string, string>,
        } as InternalAxiosRequestConfig;

        const updatedConfig = await requestInterceptor.fulfilled!(config);
        expect(updatedConfig.headers.Authorization).toBeUndefined();
    });

    it("passes through successful responses unmodified", async () => {
        // @ts-expect-error accessing internal interceptor handlers for testing
        const responseInterceptor = apiClient.interceptors.response.handlers[0];

        const mockResponse = { data: { success: true }, status: 200 } as AxiosResponse;
        const result = responseInterceptor.fulfilled!(mockResponse);
        expect(result).toBe(mockResponse);
    });

    it("does not attempt refresh on /auth/login or /auth/refresh 401s", async () => {
        // @ts-expect-error accessing internal interceptor handlers for testing
        const responseInterceptor = apiClient.interceptors.response.handlers[0];

        const error = {
            response: { status: 401, data: { error: { code: "UNAUTHORIZED", message: "Bad credentials" } } },
            config: { url: "/auth/login/" },
        };

        await expect(responseInterceptor.rejected!(error)).rejects.toBeInstanceOf(ApiError);
    });

    it("successfully refreshes token and retries failed request on 401", async () => {
        // @ts-expect-error accessing internal interceptor handlers for testing
        const responseInterceptor = apiClient.interceptors.response.handlers[0];

        const postSpy = vi.spyOn(axios, "post").mockResolvedValueOnce({
            data: { access: "new.jwt.access.token" },
        });

        const retrySpy = vi.spyOn(apiClient, "request").mockResolvedValueOnce({
            data: "retried_success",
        } as AxiosResponse);

        const error = {
            response: { status: 401 },
            config: {
                url: "/attempts/123/",
                headers: {} as Record<string, string>,
            },
        };

        const result = await responseInterceptor.rejected!(error);

        expect(postSpy).toHaveBeenCalledWith(
            expect.stringContaining("/auth/refresh/"),
            {},
            { withCredentials: true },
        );
        expect(getAccessToken()).toBe("new.jwt.access.token");
        expect(retrySpy).toHaveBeenCalled();
        expect(result.data).toBe("retried_success");
    });

    it("clears token and invokes onSessionExpired when refresh fails", async () => {
        // @ts-expect-error accessing internal interceptor handlers for testing
        const responseInterceptor = apiClient.interceptors.response.handlers[0];

        const onExpiredSpy = vi.fn();
        setOnSessionExpired(onExpiredSpy);
        setAccessToken("old.expired.token");

        vi.spyOn(axios, "post").mockRejectedValueOnce({
            response: { status: 401, data: { error: { code: "TOKEN_EXPIRED", message: "Refresh expired" } } },
        });

        const error = {
            response: { status: 401 },
            config: {
                url: "/attempts/123/",
                headers: {} as Record<string, string>,
            },
        };

        await expect(responseInterceptor.rejected!(error)).rejects.toBeInstanceOf(ApiError);
        expect(getAccessToken()).toBeNull();
        expect(onExpiredSpy).toHaveBeenCalledTimes(1);
    });
});
