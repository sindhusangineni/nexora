export type UserRole = "student" | "superadmin";

export interface AuthUser {
    id: string;
    email: string;
    email_verified: boolean;
    roles: string[];
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface LoginResponse {
    access: string;
    user: AuthUser;
}

export interface TokenRefreshResponse {
    access: string;
}

export interface LogoutResponse {
    message: string;
}

export type AuthStatus =
    | "idle"
    | "authenticating"
    | "authenticated"
    | "unauthenticated"
    | "refreshing";

export interface AuthContextValue {
    user: AuthUser | null;
    status: AuthStatus;
    isAuthenticated: boolean;
    isStudent: boolean;
    isSuperadmin: boolean;
    login: (credentials: LoginCredentials) => Promise<AuthUser>;
    logout: () => Promise<void>;
    checkAuth: () => Promise<void>;
}
