import csv
import io
import re
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Lower

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.application.questions import create_question
from apps.question_bank.models import (
    AssertionReasonRelationship,
    Difficulty,
    Question,
    QuestionSourceType,
    QuestionStatus,
    QuestionTopic,
    QuestionType,
    QuestionVersion,
)

MAX_IMPORT_ROWS = 500
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

CSV_TEMPLATE_HEADERS = [
    "question_type",
    "text",
    "difficulty",
    "topic_name",
    "chapter_name",
    "subject_name",
    "domain_name",
    "topic_id",
    "choice_a",
    "choice_b",
    "choice_c",
    "choice_d",
    "choice_e",
    "correct_answer",
    "assertion",
    "reason",
    "correct_relationship",
    "match_left_items",
    "match_right_items",
    "match_pairs",
    "marks",
    "expected_answer",
    "explanation",
    "source_type",
    "source_name",
    "source_year",
    "source_reference",
    "external_question_id",
]


@dataclass
class RowValidationError:
    row_number: int
    field: str
    message: str
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedImportRow:
    row_number: int
    raw_data: dict[str, Any]
    is_valid: bool = True
    is_duplicate: bool = False
    duplicate_type: str | None = None  # "STRONG" | "POTENTIAL"
    duplicate_reason: str | None = None
    errors: list[RowValidationError] = field(default_factory=list)

    # Validated fields for create_question
    question_type: str | None = None
    text: str | None = None
    difficulty: str | None = None
    explanation: str = ""
    topic: Topic | None = None
    source_type: str | None = None
    source_name: str | None = None
    source_year: int | None = None
    source_reference: str | None = None
    external_question_id: str | None = None

    # Type-specific payload
    choices: list[dict] | None = None
    true_false_data: dict | bool | None = None
    assertion_reason_data: dict | None = None
    match_following_data: dict | None = None
    descriptive_data: dict | None = None

    def add_error(self, field_name: str, message: str) -> None:
        self.is_valid = False
        self.errors.append(
            RowValidationError(
                row_number=self.row_number,
                field=field_name,
                message=message,
                raw_data=self.raw_data,
            )
        )


def _normalize_header(header: str) -> str:
    cleaned = header.strip().lower().replace(" ", "_").replace("-", "_")
    alias_map = {
        "type": "question_type",
        "qtype": "question_type",
        "question": "text",
        "question_text": "text",
        "stem": "text",
        "prompt": "text",
        "topic": "topic_name",
        "chapter": "chapter_name",
        "subject": "subject_name",
        "domain": "domain_name",
        "option_a": "choice_a",
        "option_b": "choice_b",
        "option_c": "choice_c",
        "option_d": "choice_d",
        "option_e": "choice_e",
        "answer": "correct_answer",
        "correct_choice": "correct_answer",
        "correct_option": "correct_answer",
        "relationship": "correct_relationship",
        "year": "source_year",
        "source": "source_type",
        "reference": "source_reference",
        "external_id": "external_question_id",
        "qid": "external_question_id",
        "rubric": "expected_answer",
        "model_answer": "expected_answer",
    }
    return alias_map.get(cleaned, cleaned)


def _normalize_text_stem(text: str) -> str:
    """
    Conservative text normalization:
    - Lowercases text
    - Normalizes and collapses Unicode whitespace (spaces, tabs, newlines)
    - Preserves all punctuation, operators, code tokens, math symbols, and brackets
    """
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


class QuestionImportEngine:
    """
    Core parsing, validation, and ingestion engine for bulk UPSC questions.
    """

    def __init__(self, file_content: str | bytes):
        self.file_content = file_content
        self._parsed_rows: list[ParsedImportRow] = []
        self._structural_errors: list[str] = []
        self._topics_cache: dict[uuid.UUID, Topic] = {}
        self._topics_by_name: dict[str, list[Topic]] = {}

    @property
    def structural_errors(self) -> list[str]:
        return list(self._structural_errors)

    @property
    def parsed_rows(self) -> list[ParsedImportRow]:
        return list(self._parsed_rows)

    def _decode_content(self) -> str:
        if isinstance(self.file_content, str):
            if "\x00" in self.file_content:
                raise ValidationError(
                    "Uploaded file contains binary content or null bytes. Only valid UTF-8 CSV text files are supported."
                )
            return self.file_content

        if b"\x00" in self.file_content:
            raise ValidationError(
                "Uploaded file contains binary content or null bytes. Only valid UTF-8 CSV text files are supported."
            )

        # Strict UTF-8 with BOM or standard UTF-8 decode
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                return self.file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValidationError("Uploaded file cannot be decoded. Please use valid UTF-8 encoding.")

    def _load_taxonomy_cache_for_batch(self, raw_rows: list[dict[str, str]]) -> None:
        """
        Scalable bounded taxonomy lookup:
        Extracts distinct topic IDs and topic names referenced in the batch,
        and issues a single bounded query with select_related to load only the
        relevant taxonomy slice into memory.
        """
        distinct_topic_ids: set[uuid.UUID] = set()
        distinct_topic_names: set[str] = set()

        for r in raw_rows:
            tid_str = r.get("topic_id", "").strip()
            if tid_str:
                try:
                    distinct_topic_ids.add(uuid.UUID(tid_str))
                except (ValueError, AttributeError):
                    pass
            tname = r.get("topic_name", "").strip()
            if tname:
                distinct_topic_names.add(tname.lower())

        query = Q()
        if distinct_topic_ids:
            query |= Q(id__in=distinct_topic_ids)
        if distinct_topic_names:
            query |= Q(name_lower__in=distinct_topic_names)

        if not query:
            self._topics_cache = {}
            self._topics_by_name = {}
            return

        topics = list(
            Topic.objects.annotate(name_lower=Lower("name"))
            .filter(query)
            .select_related("chapter__subject__domain")
        )

        self._topics_cache = {t.id: t for t in topics}
        self._topics_by_name = {}
        for t in topics:
            key = t.name.strip().lower()
            self._topics_by_name.setdefault(key, []).append(t)

    def parse_and_validate(self) -> list[ParsedImportRow]:
        content_str = self._decode_content()

        reader = csv.reader(io.StringIO(content_str))
        rows = list(reader)

        if not rows:
            self._structural_errors.append("CSV file is completely empty.")
            return []

        # Header row
        header_raw = rows[0]
        if not any(header_raw):
            self._structural_errors.append("CSV header row is empty.")
            return []

        normalized_headers = [_normalize_header(h) for h in header_raw]

        # Check essential columns
        required_cols = {"question_type", "text", "difficulty"}
        missing_cols = required_cols - set(normalized_headers)
        if missing_cols:
            self._structural_errors.append(
                f"Missing required CSV column(s): {', '.join(sorted(missing_cols))}."
            )
            return []

        data_rows = rows[1:]
        if not data_rows:
            self._structural_errors.append("CSV contains headers but no question data rows.")
            return []

        if len(data_rows) > MAX_IMPORT_ROWS:
            self._structural_errors.append(
                f"CSV exceeds maximum batch limit of {MAX_IMPORT_ROWS} rows (received {len(data_rows)} rows). Please split your import into smaller batches."
            )
            return []

        # Collect raw row dicts first
        raw_row_entries: list[tuple[int, dict[str, str]]] = []
        for row_idx, row_values in enumerate(data_rows, start=2):  # 1-indexed header is row 1
            if not any(v.strip() for v in row_values):
                continue

            raw_dict: dict[str, str] = {}
            for col_idx, h in enumerate(normalized_headers):
                val = row_values[col_idx].strip() if col_idx < len(row_values) else ""
                raw_dict[h] = val
            raw_row_entries.append((row_idx, raw_dict))

        # 1. Scalable bounded taxonomy lookup for distinct references in batch
        self._load_taxonomy_cache_for_batch([entry[1] for entry in raw_row_entries])

        # 2. Bounded pre-fetch of existing provenance keys: (source_type, external_question_id)
        distinct_external_ids = {
            entry[1].get("external_question_id", "").strip()
            for entry in raw_row_entries
            if entry[1].get("external_question_id", "").strip()
        }
        existing_provenance_keys: set[tuple[str, str]] = set()
        if distinct_external_ids:
            existing_provenance_keys = set(
                QuestionVersion.objects.filter(external_question_id__in=distinct_external_ids)
                .values_list("source_type", "external_question_id")
            )

        # 3. Bounded pre-fetch of existing question texts within the referenced topics
        distinct_clean_texts = {
            t.strip()
            for entry in raw_row_entries
            if (t := entry[1].get("text", "").strip())
        }
        distinct_lower_texts = {t.lower() for t in distinct_clean_texts}
        existing_text_topic_keys: set[tuple[str, uuid.UUID | None]] = set()
        if distinct_lower_texts and self._topics_cache:
            qt_matches = (
                QuestionTopic.objects.filter(
                    topic__in=self._topics_cache.values(),
                )
                .annotate(lower_text=Lower("question__versions__text"))
                .filter(lower_text__in=distinct_lower_texts)
                .values_list("question__versions__text", "topic_id")
                .distinct()
            )
            for txt, tid in qt_matches:
                existing_text_topic_keys.add((_normalize_text_stem(txt), tid))

        # Intra-batch duplicate tracking
        batch_provenance_keys: set[tuple[str, str]] = set()
        batch_text_topic_keys: set[tuple[str, uuid.UUID | None]] = set()

        # Build and validate parsed rows
        self._parsed_rows = []
        for row_idx, raw_dict in raw_row_entries:
            parsed_row = ParsedImportRow(row_number=row_idx, raw_data=raw_dict)
            self._validate_row(
                parsed_row,
                batch_provenance_keys,
                batch_text_topic_keys,
                existing_provenance_keys,
                existing_text_topic_keys,
            )
            self._parsed_rows.append(parsed_row)

        return self._parsed_rows

    def _validate_row(
        self,
        row: ParsedImportRow,
        batch_provenance_keys: set[tuple[str, str]],
        batch_text_topic_keys: set[tuple[str, uuid.UUID | None]],
        existing_provenance_keys: set[tuple[str, str]],
        existing_text_topic_keys: set[tuple[str, uuid.UUID | None]],
    ) -> None:
        data = row.raw_data

        # 1. Question Type
        raw_type = data.get("question_type", "").upper()
        if not raw_type:
            row.add_error("question_type", "Question type is required.")
        elif raw_type not in QuestionType.values:
            valid_types = ", ".join(QuestionType.values)
            row.add_error("question_type", f"Invalid question_type '{raw_type}'. Must be one of: {valid_types}.")
        else:
            row.question_type = raw_type

        # 2. Text (Question Stem)
        text = data.get("text", "").strip()
        if not text:
            row.add_error("text", "Question text cannot be blank.")
        else:
            row.text = text

        # 3. Difficulty
        raw_diff = data.get("difficulty", "").upper()
        if not raw_diff:
            row.add_error("difficulty", "Difficulty is required.")
        elif raw_diff not in Difficulty.values:
            valid_diffs = ", ".join(Difficulty.values)
            row.add_error("difficulty", f"Invalid difficulty '{raw_diff}'. Must be one of: {valid_diffs}.")
        else:
            row.difficulty = raw_diff

        # 4. Explanation
        row.explanation = data.get("explanation", "").strip()

        # 5. Taxonomy Resolution (Topic)
        self._resolve_taxonomy(row)

        # 6. Provenance Metadata
        self._resolve_provenance(row)

        # 7. Type-specific Validation
        if row.question_type:
            self._validate_type_content(row)

        # 8. Duplicate Detection
        self._detect_duplicates(
            row,
            batch_provenance_keys,
            batch_text_topic_keys,
            existing_provenance_keys,
            existing_text_topic_keys,
        )

    def _resolve_taxonomy(self, row: ParsedImportRow) -> None:
        data = row.raw_data
        topic_id_str = data.get("topic_id", "").strip()
        topic_name = data.get("topic_name", "").strip()
        chapter_name = data.get("chapter_name", "").strip()
        subject_name = data.get("subject_name", "").strip()

        # Strategy A: By topic_id UUID
        if topic_id_str:
            try:
                tid = uuid.UUID(topic_id_str)
            except (ValueError, AttributeError):
                row.add_error("topic_id", f"Invalid topic_id format: '{topic_id_str}'. Must be a valid UUID.")
                return

            topic = self._topics_cache.get(tid)
            if not topic:
                row.add_error("topic_id", f"Topic with ID '{topic_id_str}' does not exist in taxonomy.")
                return
            row.topic = topic
            return

        # Strategy B: By human-readable topic_name
        if not topic_name:
            row.add_error("topic_name", "Either topic_id or topic_name must be provided.")
            return

        matches = self._topics_by_name.get(topic_name.lower(), [])
        if not matches:
            row.add_error("topic_name", f'Topic "{topic_name}" was not found.')
            return

        if len(matches) == 1:
            row.topic = matches[0]
            return

        # Ambiguity resolution using chapter_name
        if chapter_name:
            filtered = [m for m in matches if m.chapter.name.strip().lower() == chapter_name.lower()]
            if len(filtered) == 1:
                row.topic = filtered[0]
                return
            if len(filtered) > 1 and subject_name:
                sub_filtered = [m for m in filtered if m.chapter.subject.name.strip().lower() == subject_name.lower()]
                if len(sub_filtered) == 1:
                    row.topic = sub_filtered[0]
                    return

        # Still ambiguous
        chapters = ", ".join(f"'{m.chapter.name}' (Subject: {m.chapter.subject.name})" for m in matches)
        row.add_error(
            "topic_name",
            f"Topic '{topic_name}' is ambiguous. It exists under multiple chapters: {chapters}. Please specify chapter_name or use topic_id.",
        )

    def _resolve_provenance(self, row: ParsedImportRow) -> None:
        data = row.raw_data
        source_type = data.get("source_type", "").upper().strip()
        source_name = data.get("source_name", "").strip()
        source_year_str = data.get("source_year", "").strip()
        source_reference = data.get("source_reference", "").strip()
        external_id = data.get("external_question_id", "").strip()

        # Parse source_year
        if source_year_str:
            try:
                year_val = int(source_year_str)
                if year_val < 1900 or year_val > 2100:
                    row.add_error("source_year", f"Invalid source_year '{source_year_str}'. Must be a 4-digit year.")
                else:
                    row.source_year = year_val
            except ValueError:
                row.add_error("source_year", f"source_year must be an integer (received '{source_year_str}').")

        # Default source_type to UPSC_PREVIOUS_YEAR if source_year is given, else ORIGINAL
        if not source_type:
            if row.source_year:
                source_type = QuestionSourceType.UPSC_PREVIOUS_YEAR
            else:
                source_type = QuestionSourceType.ORIGINAL
        elif source_type not in QuestionSourceType.values:
            valid_sources = ", ".join(QuestionSourceType.values)
            row.add_error("source_type", f"Invalid source_type '{source_type}'. Must be one of: {valid_sources}.")

        row.source_type = source_type

        # Default source_name to UPSC if UPSC_PREVIOUS_YEAR
        if not source_name and source_type == QuestionSourceType.UPSC_PREVIOUS_YEAR:
            source_name = "UPSC"

        row.source_name = source_name or None
        row.source_reference = source_reference or None
        row.external_question_id = external_id or None

    def _extract_choices(self, row: ParsedImportRow) -> list[str]:
        data = row.raw_data
        choices: list[str] = []

        # Check explicit columns choice_a, choice_b, choice_c, choice_d, choice_e
        for col_name in ("choice_a", "choice_b", "choice_c", "choice_d", "choice_e"):
            val = data.get(col_name, "").strip()
            if val:
                choices.append(val)

        # Fallback to pipe-separated choices column
        if not choices and data.get("choices", "").strip():
            raw_choices = data.get("choices", "").split("|")
            choices = [c.strip() for c in raw_choices if c.strip()]

        return choices

    def _validate_type_content(self, row: ParsedImportRow) -> None:
        qtype = row.question_type
        data = row.raw_data

        if qtype == QuestionType.MCQ:
            choices = self._extract_choices(row)
            if len(choices) < 2:
                row.add_error("choices", "MCQ must contain at least two choices.")
                return

            ans_str = data.get("correct_answer", "").strip()
            if not ans_str:
                row.add_error("correct_answer", "MCQ requires a correct_answer (e.g., 'A', 'B', 'C', 'D').")
                return

            correct_idx = self._parse_single_choice_index(ans_str, choices)
            if correct_idx is None:
                row.add_error(
                    "correct_answer",
                    f"Correct answer does not reference a supplied choice (received '{ans_str}').",
                )
                return

            row.choices = [
                {
                    "text": c_text,
                    "position": idx + 1,
                    "is_correct": (idx == correct_idx),
                }
                for idx, c_text in enumerate(choices)
            ]

        elif qtype == QuestionType.MULTIPLE_SELECT:
            choices = self._extract_choices(row)
            if len(choices) < 2:
                row.add_error("choices", f"MULTIPLE_SELECT requires at least 2 choices (found {len(choices)}).")
                return

            ans_str = data.get("correct_answer", "").strip()
            if not ans_str:
                row.add_error("correct_answer", "MULTIPLE_SELECT requires at least one correct_answer (e.g., 'A, B').")
                return

            correct_indices = self._parse_multiple_choice_indices(ans_str, choices)
            if not correct_indices:
                row.add_error(
                    "correct_answer",
                    f"correct_answer '{ans_str}' did not match any valid choices.",
                )
                return

            row.choices = [
                {
                    "text": c_text,
                    "position": idx + 1,
                    "is_correct": (idx in correct_indices),
                }
                for idx, c_text in enumerate(choices)
            ]

        elif qtype == QuestionType.TRUE_FALSE:
            ans_str = data.get("correct_answer", "").strip().lower()
            if ans_str in ("true", "t", "1", "yes"):
                row.true_false_data = {"answer": True}
            elif ans_str in ("false", "f", "0", "no"):
                row.true_false_data = {"answer": False}
            else:
                row.add_error(
                    "correct_answer",
                    f"TRUE_FALSE question requires 'TRUE' or 'FALSE' as correct_answer (received '{data.get('correct_answer', '')}').",
                )

        elif qtype == QuestionType.ASSERTION_REASON:
            assertion = data.get("assertion", "").strip()
            reason = data.get("reason", "").strip()
            rel_str = data.get("correct_relationship", "").strip().upper()

            if not assertion:
                row.add_error("assertion", "ASSERTION_REASON requires a non-empty 'assertion' statement.")
            if not reason:
                row.add_error("reason", "ASSERTION_REASON requires a non-empty 'reason' statement.")

            # Map shorthand A, B, C, D to standard AssertionReasonRelationship
            rel_map = {
                "A": AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
                "1": AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
                AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT: AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
                "B": AssertionReasonRelationship.BOTH_TRUE_REASON_NOT_CORRECT,
                "2": AssertionReasonRelationship.BOTH_TRUE_REASON_NOT_CORRECT,
                AssertionReasonRelationship.BOTH_TRUE_REASON_NOT_CORRECT: AssertionReasonRelationship.BOTH_TRUE_REASON_NOT_CORRECT,
                "C": AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE,
                "3": AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE,
                AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE: AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE,
                "D": AssertionReasonRelationship.ASSERTION_FALSE_REASON_FALSE,
                "4": AssertionReasonRelationship.ASSERTION_FALSE_REASON_FALSE,
                AssertionReasonRelationship.ASSERTION_FALSE_REASON_FALSE: AssertionReasonRelationship.ASSERTION_FALSE_REASON_FALSE,
            }

            resolved_rel = rel_map.get(rel_str)
            if not resolved_rel:
                row.add_error(
                    "correct_relationship",
                    f"Invalid correct_relationship '{rel_str}'. Must be 'A', 'B', 'C', 'D' or standard enum key.",
                )
            else:
                row.assertion_reason_data = {
                    "assertion": assertion,
                    "reason": reason,
                    "correct_relationship": resolved_rel,
                }

        elif qtype == QuestionType.MATCH_FOLLOWING:
            left_str = data.get("match_left_items", "").strip()
            right_str = data.get("match_right_items", "").strip()
            pairs_str = data.get("match_pairs", "").strip()

            if not left_str:
                row.add_error("match_left_items", "MATCH_FOLLOWING requires 'match_left_items' (pipe-separated).")
            if not right_str:
                row.add_error("match_right_items", "MATCH_FOLLOWING requires 'match_right_items' (pipe-separated).")
            if not pairs_str:
                row.add_error("match_pairs", "MATCH_FOLLOWING requires 'match_pairs' (e.g., '1:A, 2:B').")

            if not (left_str and right_str and pairs_str):
                return

            left_items = [re.sub(r"^\d+[\.\)]\s*", "", item.strip()) for item in left_str.split("|") if item.strip()]
            right_items = [re.sub(r"^[a-zA-Z\d]+[\.\)]\s*", "", item.strip()) for item in right_str.split("|") if item.strip()]

            if len(left_items) < 2:
                row.add_error("match_left_items", f"Must provide at least 2 left items (found {len(left_items)}).")
                return
            if len(right_items) < 2:
                row.add_error("match_right_items", f"Must provide at least 2 right items (found {len(right_items)}).")
                return

            # Parse pairs: e.g. "1:1, 2:2, 3:3" or "1:A, 2:B" or "1-1; 2-2"
            pairs: list[dict[str, int]] = []
            raw_pair_tokens = re.split(r"[,;]", pairs_str)
            for pt in raw_pair_tokens:
                pt = pt.strip()
                if not pt:
                    continue
                m = re.match(r"^(\d+)\s*[:=\-]\s*([a-zA-Z\d]+)$", pt)
                if not m:
                    row.add_error("match_pairs", f"Invalid pair format '{pt}'. Expected 'left:right' (e.g., '1:A' or '1:1').")
                    return

                l_pos = int(m.group(1))
                r_token = m.group(2)

                # Right token can be digit (1-indexed) or letter (A=1, B=2, ...)
                if r_token.isdigit():
                    r_pos = int(r_token)
                elif len(r_token) == 1 and r_token.upper().isalpha():
                    r_pos = ord(r_token.upper()) - 64
                else:
                    row.add_error("match_pairs", f"Invalid right-side reference in pair '{pt}'.")
                    return

                if l_pos < 1 or l_pos > len(left_items):
                    row.add_error("match_pairs", f"Left item position {l_pos} out of range (1-{len(left_items)}).")
                    return
                if r_pos < 1 or r_pos > len(right_items):
                    row.add_error("match_pairs", f"Right item position {r_pos} out of range (1-{len(right_items)}).")
                    return

                pairs.append({"left_position": l_pos, "right_position": r_pos})

            if not pairs:
                row.add_error("match_pairs", "No valid matching pairs parsed.")
                return

            row.match_following_data = {
                "left_items": [{"position": i + 1, "text": t} for i, t in enumerate(left_items)],
                "right_items": [{"position": i + 1, "text": t} for i, t in enumerate(right_items)],
                "pairs": pairs,
            }

        elif qtype == QuestionType.DESCRIPTIVE:
            marks_str = data.get("marks", "").strip()
            marks_val = Decimal("10.00")
            if marks_str:
                try:
                    marks_val = Decimal(marks_str)
                    if marks_val <= 0:
                        row.add_error("marks", f"Marks must be greater than zero (received '{marks_str}').")
                except (InvalidOperation, ValueError):
                    row.add_error("marks", f"Invalid marks numeric value: '{marks_str}'.")

            row.descriptive_data = {
                "marks": marks_val,
                "expected_answer": data.get("expected_answer", "").strip(),
            }

    def _parse_single_choice_index(self, ans_str: str, choices: list[str]) -> int | None:
        trimmed = ans_str.strip()
        # Single letter A, B, C, D...
        if len(trimmed) == 1 and trimmed.isalpha():
            idx = ord(trimmed.upper()) - 65
            if 0 <= idx < len(choices):
                return idx
        # Numeric 1, 2, 3...
        if trimmed.isdigit():
            idx = int(trimmed) - 1
            if 0 <= idx < len(choices):
                return idx
        # Exact text match
        for idx, c in enumerate(choices):
            if c.lower() == trimmed.lower():
                return idx
        return None

    def _parse_multiple_choice_indices(self, ans_str: str, choices: list[str]) -> set[int]:
        tokens = [t.strip() for t in re.split(r"[,|;]", ans_str) if t.strip()]
        indices: set[int] = set()
        for tok in tokens:
            idx = self._parse_single_choice_index(tok, choices)
            if idx is not None:
                indices.add(idx)
        return indices

    def _detect_duplicates(
        self,
        row: ParsedImportRow,
        batch_provenance_keys: set[tuple[str, str]],
        batch_text_topic_keys: set[tuple[str, uuid.UUID | None]],
        existing_provenance_keys: set[tuple[str, str]],
        existing_text_topic_keys: set[tuple[str, uuid.UUID | None]],
    ) -> None:
        # Check external_question_id (authoritative provenance identity)
        ext_id = (row.external_question_id or "").strip()
        source_type = row.source_type or ""
        if ext_id:
            prov_key = (source_type, ext_id)
            # Check intra-batch external ID duplicate
            if prov_key in batch_provenance_keys or any(eid == ext_id for _, eid in batch_provenance_keys):
                row.is_duplicate = True
                row.duplicate_type = "STRONG"
                row.duplicate_reason = (
                    f"Duplicate external_question_id '{ext_id}' repeated within this CSV batch."
                )
                return
            # Check DB existing external ID duplicate scoped to source
            if prov_key in existing_provenance_keys or any(eid == ext_id for _, eid in existing_provenance_keys):
                row.is_duplicate = True
                row.duplicate_type = "STRONG"
                row.duplicate_reason = (
                    f"Question with external_question_id '{ext_id}' (source: {source_type}) already exists in Question Bank."
                )
                return
            batch_provenance_keys.add(prov_key)

        # Check question stem and topic
        if row.text:
            stem = _normalize_text_stem(row.text)
            topic_id = row.topic.id if row.topic else None
            if stem:
                text_topic_key = (stem, topic_id)
                # Check intra-batch text stem collision within the same topic
                if text_topic_key in batch_text_topic_keys:
                    row.is_duplicate = True
                    row.duplicate_type = "STRONG"
                    row.duplicate_reason = "Identical question stem within the same topic repeated within this CSV batch."
                    return

                # Check DB for existing text stem in the same topic
                if text_topic_key in existing_text_topic_keys:
                    # Potential textual duplicate: classify and report without suppressing
                    row.is_duplicate = False
                    row.duplicate_type = "POTENTIAL"
                    topic_label = f"topic '{row.topic.name}'" if row.topic else "the same topic"
                    row.duplicate_reason = f"Potential textual similarity with an existing question in {topic_label}."
                    return

                batch_text_topic_keys.add(text_topic_key)


def preview_question_import(file_content: str | bytes) -> dict[str, Any]:
    """
    Parses and validates CSV content without database modifications.
    Returns preview summary, validation errors, and row previews.
    """
    engine = QuestionImportEngine(file_content)
    rows = engine.parse_and_validate()

    if engine._structural_errors:
        return {
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "duplicate_rows": 0,
            "can_import": False,
            "summary": {},
            "errors": [
                {
                    "row_number": 0,
                    "field": "file",
                    "message": msg,
                    "raw_data": {},
                }
                for msg in engine._structural_errors
            ],
            "rows": [],
        }

    total_rows = len(rows)
    valid_rows = sum(1 for r in rows if r.is_valid and not r.is_duplicate)
    duplicate_rows = sum(1 for r in rows if r.is_duplicate)
    invalid_rows = sum(1 for r in rows if not r.is_valid)

    # Type summary
    type_counts: dict[str, int] = {}
    for r in rows:
        if r.question_type:
            type_counts[r.question_type] = type_counts.get(r.question_type, 0) + 1

    # Flatten errors
    all_errors = []
    for r in rows:
        for err in r.errors:
            all_errors.append(
                {
                    "row_number": err.row_number,
                    "field": err.field,
                    "message": err.message,
                    "raw_data": err.raw_data,
                }
            )

    rows_preview = []
    for r in rows:
        rows_preview.append(
            {
                "row_number": r.row_number,
                "is_valid": r.is_valid,
                "is_duplicate": r.is_duplicate,
                "duplicate_type": r.duplicate_type,
                "duplicate_reason": r.duplicate_reason,
                "question_type": r.question_type,
                "text": (r.text[:120] + "...") if r.text and len(r.text) > 120 else (r.text or ""),
                "difficulty": r.difficulty,
                "topic_name": r.topic.name if r.topic else r.raw_data.get("topic_name", ""),
                "topic_id": str(r.topic.id) if r.topic else None,
                "source_type": r.source_type,
                "source_year": r.source_year,
                "external_question_id": r.external_question_id,
                "errors": [e.message for e in r.errors],
            }
        )

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
        "can_import": (invalid_rows == 0 and (valid_rows > 0 or duplicate_rows > 0)),
        "summary": type_counts,
        "errors": all_errors,
        "rows": rows_preview,
    }


@transaction.atomic
def execute_question_import(
    file_content: str | bytes,
    *,
    skip_duplicates: bool = True,
) -> dict[str, Any]:
    """
    Executes the validated import batch inside an atomic transaction.
    Option A (All-or-Nothing): If any row contains validation errors, the import fails.
    Reuses existing Question Bank use-case `create_question`.
    Questions are created strictly as DRAFT.
    """
    engine = QuestionImportEngine(file_content)
    rows = engine.parse_and_validate()

    if engine._structural_errors:
        raise ValidationError(f"Structural error: {'; '.join(engine._structural_errors)}")

    invalid_rows = [r for r in rows if not r.is_valid]
    if invalid_rows:
        error_msgs = [f"Row {r.row_number}: {'; '.join(e.message for e in r.errors)}" for r in invalid_rows[:5]]
        raise ValidationError(
            f"Cannot import batch with {len(invalid_rows)} invalid row(s). Errors: {'; '.join(error_msgs)}"
        )

    imported_count = 0
    skipped_count = 0
    created_question_ids: list[str] = []

    for row in rows:
        if row.is_duplicate and row.duplicate_type == "STRONG":
            if skip_duplicates:
                skipped_count += 1
                continue
            else:
                raise ValidationError(f"Row {row.row_number}: {row.duplicate_reason}")

        # Execute creation via existing domain use case
        topic_ids = [str(row.topic.id)] if row.topic else []
        question = create_question(
            question_type=row.question_type or QuestionType.MCQ,
            text=row.text or "",
            difficulty=row.difficulty or Difficulty.MEDIUM,
            explanation=row.explanation,
            topic_ids=topic_ids,
            source_type=row.source_type,
            source_name=row.source_name,
            source_reference=row.source_reference,
            source_year=row.source_year,
            external_question_id=row.external_question_id,
            choices=row.choices,
            true_false_data=row.true_false_data,
            assertion_reason_data=row.assertion_reason_data,
            match_following_data=row.match_following_data,
            descriptive_data=row.descriptive_data,
        )
        imported_count += 1
        created_question_ids.append(str(question.id))

    return {
        "total_rows": len(rows),
        "imported_rows": imported_count,
        "skipped_rows": skipped_count,
        "failed_rows": 0,
        "created_question_ids": created_question_ids,
        "errors": [],
    }


def generate_csv_template() -> str:
    """
    Generates a production-ready CSV template containing headers and
    illustrative sample rows for all six question types.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_TEMPLATE_HEADERS)

    # 1. MCQ Sample Row
    writer.writerow([
        "MCQ",
        "With reference to the Constitution of India, which one of the following rights was described by Dr. B.R. Ambedkar as the 'heart and soul of the Constitution'?",
        "MEDIUM",
        "Fundamental Rights",
        "Constitution & Fundamental Rights",
        "Polity",
        "General Studies",
        "",  # topic_id optional
        "Right to Freedom of Religion",
        "Right to Property",
        "Right to Equality",
        "Right to Constitutional Remedies",
        "",  # choice_e
        "D",  # correct_answer
        "", "", "",  # assertion, reason, correct_relationship
        "", "", "",  # match items & pairs
        "", "",  # marks, expected_answer
        "Article 32 provides the right to constitutional remedies, described as the heart and soul by Ambedkar.",
        "UPSC_PREVIOUS_YEAR",
        "UPSC",
        "2022",
        "Civil Services Preliminary Examination 2022 Paper I",
        "UPSC-CSE-2022-GS1-Q15",
    ])

    # 2. MULTIPLE_SELECT Sample Row
    writer.writerow([
        "MULTIPLE_SELECT",
        "Which of the following are tributaries of the Indus River flowing through Jammu and Kashmir or Ladakh?",
        "HARD",
        "Drainage System",
        "Physical Geography",
        "Geography",
        "General Studies",
        "",
        "Shyok River",
        "Zanskar River",
        "Gilgit River",
        "Gomati River",
        "",
        "A, B, C",
        "", "", "",
        "", "", "",
        "", "",
        "Shyok, Zanskar, and Gilgit are Indus tributaries. Gomati is a tributary of the Ganges.",
        "UPSC_PREVIOUS_YEAR",
        "UPSC",
        "2021",
        "Civil Services Preliminary Examination 2021",
        "UPSC-CSE-2021-GS1-Q28",
    ])

    # 3. TRUE_FALSE Sample Row
    writer.writerow([
        "TRUE_FALSE",
        "The Governor of a State has the constitutional power to grant pardon in cases of death sentence under Article 161.",
        "EASY",
        "Union & State Executive",
        "State Government",
        "Polity",
        "General Studies",
        "",
        "", "", "", "", "",
        "FALSE",
        "", "", "",
        "", "", "",
        "", "",
        "The President alone has the power to pardon a death sentence under Article 72. The Governor cannot pardon a death sentence.",
        "ORIGINAL",
        "Nexora Editorial",
        "2024",
        "Nexora UPSC Polity Revision Set",
        "NEX-POL-TF-001",
    ])

    # 4. ASSERTION_REASON Sample Row
    writer.writerow([
        "ASSERTION_REASON",
        "Consider the following statements regarding the Attorney General for India:",
        "MEDIUM",
        "Constitutional Bodies",
        "Constitutional & Non-Constitutional Bodies",
        "Polity",
        "General Studies",
        "",
        "", "", "", "", "",
        "",
        "The Attorney General for India has the right to speak and take part in the proceedings of either House of Parliament.",
        "The Attorney General has the right to vote in parliamentary joint sittings under Article 88.",
        "C",  # Assertion is true, but Reason is false
        "", "", "",
        "", "",
        "Under Article 88, the Attorney General can speak and take part in proceedings but cannot vote.",
        "UPSC_PREVIOUS_YEAR",
        "UPSC",
        "2019",
        "Civil Services Preliminary Examination 2019",
        "UPSC-CSE-2019-GS1-Q54",
    ])

    # 5. MATCH_FOLLOWING Sample Row
    writer.writerow([
        "MATCH_FOLLOWING",
        "Match the following Biosphere Reserves with their respective States:",
        "HARD",
        "Ecology & Biodiversity",
        "Environment & Ecology",
        "Environment",
        "General Studies",
        "",
        "", "", "", "", "",
        "",
        "", "", "",
        "1. Dehong-Debang | 2. Nokrek | 3. Simlipal",
        "A. Arunachal Pradesh | B. Meghalaya | C. Odisha",
        "1:A, 2:B, 3:C",
        "", "",
        "Dehong-Debang is in Arunachal Pradesh, Nokrek is in Meghalaya, and Simlipal is in Odisha.",
        "UPSC_PREVIOUS_YEAR",
        "UPSC",
        "2020",
        "Civil Services Preliminary Examination 2020",
        "UPSC-CSE-2020-GS1-Q72",
    ])

    # 6. DESCRIPTIVE Sample Row
    writer.writerow([
        "DESCRIPTIVE",
        "Critically evaluate the significance of the 73rd Constitutional Amendment Act in empowering Panchayati Raj Institutions in India. (Answer in 250 words)",
        "HARD",
        "Local Self Government",
        "Panchayati Raj & Local Governance",
        "Polity",
        "General Studies",
        "",
        "", "", "", "", "",
        "",
        "", "", "",
        "", "", "",
        "15",
        "Key aspects: Constitutional status, 3-tier structure, reservation for women, financial devolution challenges, 3Fs (Funds, Functions, Functionaries).",
        "UPSC Mains GS Paper 2 analytical question.",
        "UPSC_PREVIOUS_YEAR",
        "UPSC",
        "2023",
        "Civil Services Main Examination 2023 GS Paper II",
        "UPSC-CSE-2023-GS2-Q04",
    ])

    return output.getvalue()
