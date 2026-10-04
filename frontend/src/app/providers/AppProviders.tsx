import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { AuthProvider } from "@/features/auth";
import { queryClient } from "@/lib/query/client";

interface AppProvidersProps {
    children: ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                {children}
            </AuthProvider>
        </QueryClientProvider>
    );
}
