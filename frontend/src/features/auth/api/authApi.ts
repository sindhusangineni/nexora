import { apiClient } from "@/lib/api";
import type {
    LoginCredentials,
    LoginResponse,
    LogoutResponse,
    RegisterPayload,
    RegisterResponse,
    TokenRefreshResponse,
} from "../types/auth.types";

export const authApi = {
    async register(payload: RegisterPayload): Promise<RegisterResponse> {
        const response = await apiClient.post<RegisterResponse>(
            "/auth/register/",
            payload,
        );
        return response.data;
    },

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
