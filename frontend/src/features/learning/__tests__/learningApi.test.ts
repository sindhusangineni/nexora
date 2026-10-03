import { describe, it, expect, vi, beforeEach } from "vitest";

import { apiClient } from "@/lib/api";
import { learningApi } from "../api/learningApi";

describe("learningApi", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe("Domains API", () => {
        it("calls GET /learning/domains/ with cleaned params", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { count: 1, next: null, previous: null, results: [] },
            });

            await learningApi.getDomains({ search: "UPSC", page: 1 });

            expect(getSpy).toHaveBeenCalledWith("/learning/domains/", {
                params: { search: "UPSC", page: 1 },
            });
        });

        it("calls GET /learning/domains/:id/", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { id: "domain-1", name: "UPSC" },
            });

            const result = await learningApi.getDomain("domain-1");

            expect(getSpy).toHaveBeenCalledWith("/learning/domains/domain-1/");
            expect(result.id).toBe("domain-1");
        });

        it("calls POST /learning/domains/ for creation", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "domain-1", name: "UPSC", description: "Civil services" },
            });

            const result = await learningApi.createDomain({
                name: "UPSC",
                description: "Civil services",
            });

            expect(postSpy).toHaveBeenCalledWith("/learning/domains/", {
                name: "UPSC",
                description: "Civil services",
            });
            expect(result.name).toBe("UPSC");
        });

        it("calls PATCH /learning/domains/:id/ for updates", async () => {
            const patchSpy = vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
                data: { id: "domain-1", name: "UPSC Updated" },
            });

            const result = await learningApi.updateDomain("domain-1", {
                name: "UPSC Updated",
            });

            expect(patchSpy).toHaveBeenCalledWith("/learning/domains/domain-1/", {
                name: "UPSC Updated",
            });
            expect(result.name).toBe("UPSC Updated");
        });

        it("calls DELETE /learning/domains/:id/", async () => {
            const deleteSpy = vi.spyOn(apiClient, "delete").mockResolvedValueOnce({});

            await learningApi.deleteDomain("domain-1");

            expect(deleteSpy).toHaveBeenCalledWith("/learning/domains/domain-1/");
        });
    });

    describe("Subjects API", () => {
        it("calls GET /learning/subjects/ with domain filter", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { count: 0, next: null, previous: null, results: [] },
            });

            await learningApi.getSubjects({ domain: "domain-1" });

            expect(getSpy).toHaveBeenCalledWith("/learning/subjects/", {
                params: { domain: "domain-1" },
            });
        });

        it("calls POST /learning/subjects/ with payload", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "subject-1", name: "History", domain: "domain-1", position: 1 },
            });

            const result = await learningApi.createSubject({
                domain: "domain-1",
                name: "History",
                position: 1,
            });

            expect(postSpy).toHaveBeenCalledWith("/learning/subjects/", {
                domain: "domain-1",
                name: "History",
                position: 1,
            });
            expect(result.id).toBe("subject-1");
        });
    });

    describe("Chapters API", () => {
        it("calls GET /learning/chapters/ with subject filter", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { count: 0, next: null, previous: null, results: [] },
            });

            await learningApi.getChapters({ subject: "subject-1" });

            expect(getSpy).toHaveBeenCalledWith("/learning/chapters/", {
                params: { subject: "subject-1" },
            });
        });

        it("calls POST /learning/chapters/ with payload", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "ch-1", name: "Modern India", subject: "subject-1", position: 0 },
            });

            const result = await learningApi.createChapter({
                subject: "subject-1",
                name: "Modern India",
            });

            expect(postSpy).toHaveBeenCalledWith("/learning/chapters/", {
                subject: "subject-1",
                name: "Modern India",
            });
            expect(result.name).toBe("Modern India");
        });
    });

    describe("Topics API", () => {
        it("calls GET /learning/topics/ with chapter filter", async () => {
            const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
                data: { count: 0, next: null, previous: null, results: [] },
            });

            await learningApi.getTopics({ chapter: "ch-1" });

            expect(getSpy).toHaveBeenCalledWith("/learning/topics/", {
                params: { chapter: "ch-1" },
            });
        });

        it("calls POST /learning/topics/ with payload", async () => {
            const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
                data: { id: "top-1", name: "Quit India", chapter: "ch-1", position: 1 },
            });

            const result = await learningApi.createTopic({
                chapter: "ch-1",
                name: "Quit India",
                position: 1,
            });

            expect(postSpy).toHaveBeenCalledWith("/learning/topics/", {
                chapter: "ch-1",
                name: "Quit India",
                position: 1,
            });
            expect(result.id).toBe("top-1");
        });
    });
});
