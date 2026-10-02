import axios from "axios";

import { env } from "@/app/config/env";

export const httpClient = axios.create({
    baseURL: env.apiBaseUrl,
    headers: {
        "Content-Type": "application/json",
    },
});