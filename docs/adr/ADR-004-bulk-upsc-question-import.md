# ADR-004: Bulk UPSC Question Import Architecture & Ingestion Pipeline

## Status
**Accepted**

## Date
2026-10-04

## Context
Nexora requires an administrative bulk import mechanism for UPSC previous-year questions and original editorial questions. The platform operates as a Domain-Oriented Modular Monolith adhering to Clean/Hexagonal architecture principles with Django + DRF, PostgreSQL, and React + Vite. The Question Bank module owns the question lifecycle and Question ↔ Topic associations. Background queue infrastructure (such as Celery, Redis, or microservices) is explicitly forbidden per project guidelines.

## Architectural Decisions

### 1. Ingestion Pipeline & Clean Architecture Separation
The bulk import pipeline is structured into strictly decoupled phases:
`Upload` → `Decode & Parse` → `Structural Validation` → `Taxonomy Resolution` → `Question-Type Validation` → `Duplicate Detection` → `Preview` → `Explicit Execution Transaction`.

- The API view layer (`QuestionImportViewSet`) handles authentication, RBAC authorization (`IsSuperadminOnly`), file size/format checks, and response serialization.
- The view layer never directly mutates or accesses database tables.
- All database creation reuses the existing Question Bank domain/application use-case `create_question()`, preserving all domain invariants, content validators, and QuestionTopic mapping.

### 2. Transaction Semantics: Option A (All-or-Nothing)
We evaluated two transaction options:
- **Option A (All-or-Nothing)**: The entire batch is validated beforehand. If any row contains a validation error or unresolved taxonomy reference, execution fails atomically and rolls back completely.
- **Option B (Partial Import)**: Valid rows are committed while invalid rows are skipped and returned as errors.

**Decision**: We chose **Option A (All-or-Nothing)** for V1:
- For a high-stakes assessment platform like UPSC, partial imports risk breaking batch integrity (e.g. importing half of a 100-question paper set).
- Option A provides total administrative predictability: an import preview must be 100% clean (`invalid_rows == 0`) before explicit execution can proceed.
- Duplicate questions can be optionally skipped without failing the batch if the admin checks `skip_duplicates=True`.

### 3. Strict DRAFT Lifecycle Enactment
Imported questions are created strictly as `DRAFT` in Version 1. The import pipeline never automatically publishes or approves questions, nor does it bypass review states. All questions must traverse the standard editorial lifecycle (`DRAFT` → `REVIEW` → `APPROVED` → `PUBLISHED`).

### 4. Scalable & Deterministic Taxonomy Resolution
- Taxonomies are referenced via `topic_id` (UUID) or human-readable names (`topic_name`, `chapter_name`, `subject_name`, `domain_name`).
- Rather than loading the entire Nexora taxonomy into memory, the engine parses distinct taxonomy references required by the uploaded batch (<= 500 rows) and executes a single bounded/batched query with `select_related("chapter__subject__domain")`.
- Caches only the relevant resolution results for that import, preserving the no-N+1 property while scaling with the batch size rather than total future taxonomy size.
- If a `topic_name` is ambiguous across multiple chapters, the engine explicitly requires `chapter_name` (and `subject_name` if needed) to disambiguate. If ambiguity remains, an explicit row-level error is raised.
- Missing taxonomy entities are **never** silently created.

### 5. Conservative Duplicate Detection Semantics
We distinguish between authoritative provenance duplicates and potential textual matches:
1. **Strong Duplicate (Authoritative Provenance)**:
   - Scoped to `(source_type, external_question_id)`.
   - When an external question identifier is present, it acts as the authoritative idempotency signal.
   - Also applies to intra-batch collisions where two rows share identical provenance or identical question stem and topic within the uploaded file.
   - When `skip_duplicates=True`, genuine strong duplicates are safely skipped during execution. When `skip_duplicates=False`, they abort the import.
2. **Potential Textual Duplicate (Advisory Match)**:
   - Normalization is strictly conservative: lowercase conversion and whitespace collapsing only (`" ".join(text.strip().lower().split())`). Meaningful operators (`==`, `!=`, `<`, `>`), math symbols, code syntax, and punctuation are strictly preserved.
   - Normalized text equality against existing database questions in the same topic is classified and reported as an advisory match (`duplicate_type="POTENTIAL"`).
   - Potential textual matches are **never** automatically suppressed or skipped during execution, ensuring legitimate questions are not silently lost.

### 6. CSV Contract & Question Type Coverage
The format is CSV-first with standardized header aliasing. All six supported Question Bank types are validated with their respective content specifications:
- `MCQ`: Stem, at least 2 choices, valid correct answer reference.
- `MULTIPLE_SELECT`: Stem, multiple choices, one or more comma-separated correct answers.
- `TRUE_FALSE`: Stem, boolean answer (`TRUE`/`FALSE`).
- `ASSERTION_REASON`: Stem, assertion statement, reason statement, correct relationship code (`A`, `B`, `C`, `D`).
- `MATCH_FOLLOWING`: Stem, pipe-separated left items, pipe-separated right items, pair mappings (e.g. `1:A, 2:B`).
- `DESCRIPTIVE`: Stem, positive numeric marks, model answer / scoring rubric.

## Consequences
- **Positive**: 100% architectural alignment; no external queues or Redis needed; rock-solid transactional safety; seamless integration with Question Bank editorial review.
- **Negative / Constraints**: V1 synchronous-import safety limits of 500 rows / 5 MB per CSV batch serve as operational safeguards to preserve system responsiveness without background workers. Larger datasets must be imported in sequential batches.
