import { apiClient } from "@/lib/api";
import type {
    LoginCredentials,
    LoginResponse,
    LogoutResponse,
    TokenRefreshResponse,
} from "../types/auth.types";

export const authApi = {
    async login(credentials: LoginCredentials): Promise<LoginResponse> {
        const response = await apiClient.post<LoginResponse>(
            "/auth/login/",
            credentials,
        );
        return response.data;
    },

    async refreshToken(): Promise<TokenRefreshResponse> {
        const response = await apiClient.post<TokenRefreshResponse>(
            "/auth/refresh/",
            {},
        );
        return response.data;
    },

    async logout(): Promise<LogoutResponse> {
        const response = await apiClient.post<LogoutResponse>(
            "/auth/logout/",
            {},
        );
        return response.data;
    },
};
