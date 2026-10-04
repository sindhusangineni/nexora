import {
    useCallback,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { setAccessToken, setOnSessionExpired } from "@/lib/api";
import { authApi } from "../api/authApi";
import { AuthContext } from "./authContextDef";
import type {
    AuthContextValue,
    AuthStatus,
    AuthUser,
    LoginCredentials,
} from "../types/auth.types";

const SESSION_STORAGE_KEY = "nexora_user_session";

function loadUserSession(): AuthUser | null {
    try {
        const item = sessionStorage.getItem(SESSION_STORAGE_KEY) || localStorage.getItem(SESSION_STORAGE_KEY);
        return item ? (JSON.parse(item) as AuthUser) : null;
    } catch {
        return null;
    }
}

function saveUserSession(user: AuthUser | null): void {
    try {
        if (user) {
            sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(user));
            localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(user));
        } else {
            sessionStorage.removeItem(SESSION_STORAGE_KEY);
            localStorage.removeItem(SESSION_STORAGE_KEY);
        }
    } catch {
        // Ignore storage errors
    }
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(() => loadUserSession());
    const [status, setStatus] = useState<AuthStatus>("refreshing");
    const queryClient = useQueryClient();

    const handleSessionExpired = useCallback(() => {
        setAccessToken(null);
        setUser(null);
        saveUserSession(null);
        setStatus("unauthenticated");
        queryClient.clear();
    }, [queryClient]);

    // Register session expired callback with API client
    useEffect(() => {
        setOnSessionExpired(handleSessionExpired);
        return () => {
            setOnSessionExpired(null);
        };
    }, [handleSessionExpired]);

    // Re-verify session on mount
    useEffect(() => {
        let isMounted = true;

        authApi.refreshToken()
            .then((response) => {
                if (!isMounted) return;
                setAccessToken(response.access);

                const savedUser = loadUserSession();
                if (savedUser) {
                    setUser(savedUser);
                }
                setStatus("authenticated");
            })
            .catch(() => {
                if (!isMounted) return;
                setAccessToken(null);
                setUser(null);
                saveUserSession(null);
                setStatus("unauthenticated");
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const checkAuth = useCallback(async (): Promise<void> => {
        setStatus("refreshing");
        try {
            const response = await authApi.refreshToken();
            setAccessToken(response.access);

            const savedUser = loadUserSession();
            if (savedUser) {
                setUser(savedUser);
            }
            setStatus("authenticated");
        } catch {
            setAccessToken(null);
            setUser(null);
            saveUserSession(null);
            setStatus("unauthenticated");
        }
    }, []);

    const login = useCallback(
        async (credentials: LoginCredentials): Promise<AuthUser> => {
            setStatus("authenticating");
            try {
                const response = await authApi.login(credentials);
                setAccessToken(response.access);
                setUser(response.user);
                saveUserSession(response.user);
                setStatus("authenticated");
                return response.user;
            } catch (error) {
                setAccessToken(null);
                setUser(null);
                saveUserSession(null);
                setStatus("unauthenticated");
                throw error;
            }
        },
        [],
    );

    const logout = useCallback(async (): Promise<void> => {
        try {
            await authApi.logout();
        } catch {
            // Proceed with local cleanup even if network request fails
        } finally {
            handleSessionExpired();
        }
    }, [handleSessionExpired]);

    const isStudent = useMemo(() => {
        if (!user?.roles) return false;
        return user.roles.some((role) => role.toLowerCase() === "student");
    }, [user]);

    const isSuperadmin = useMemo(() => {
        if (!user?.roles) return false;
        return user.roles.some((role) => role.toLowerCase() === "superadmin");
    }, [user]);

    const isAuthenticated = useMemo(() => {
        return status === "authenticated" && user !== null;
    }, [status, user]);

    const contextValue = useMemo<AuthContextValue>(
        () => ({
            user,
            status,
            isAuthenticated,
            isStudent,
            isSuperadmin,
            login,
            logout,
            checkAuth,
        }),
        [user, status, isAuthenticated, isStudent, isSuperadmin, login, logout, checkAuth],
    );

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
}
