import csv
import io
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.application.question_import import (
    CSV_TEMPLATE_HEADERS,
    MAX_IMPORT_ROWS,
    QuestionImportEngine,
    execute_question_import,
    generate_csv_template,
    preview_question_import,
)
from apps.question_bank.models import (
    AssertionReasonRelationship,
    Difficulty,
    Question,
    QuestionSourceType,
    QuestionStatus,
    QuestionType,
    QuestionVersion,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    user = User.objects.create_user(email="student@nexora.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_user():
    user = User.objects.create_user(email="superadmin@nexora.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def taxonomy_tree():
    domain = Domain.objects.create(name="Civil Services Exam")
    subject = Subject.objects.create(domain=domain, name="Indian Polity")
    chapter1 = Chapter.objects.create(subject=subject, name="Fundamental Rights")
    chapter2 = Chapter.objects.create(subject=subject, name="Directive Principles")
    
    topic1 = Topic.objects.create(chapter=chapter1, name="Right to Equality")
    topic2 = Topic.objects.create(chapter=chapter1, name="Right to Freedom")
    topic3 = Topic.objects.create(chapter=chapter2, name="Socialistic Principles")
    
    # Create duplicate topic name under different chapter for ambiguity testing
    subject2 = Subject.objects.create(domain=domain, name="Modern History")
    chapter3 = Chapter.objects.create(subject=subject2, name="National Movement")
    topic_ambiguous_1 = Topic.objects.create(chapter=chapter1, name="Common Topics")
    topic_ambiguous_2 = Topic.objects.create(chapter=chapter3, name="Common Topics")

    return {
        "domain": domain,
        "subject": subject,
        "chapter1": chapter1,
        "chapter2": chapter2,
        "topic1": topic1,
        "topic2": topic2,
        "topic3": topic3,
        "topic_ambiguous_1": topic_ambiguous_1,
        "topic_ambiguous_2": topic_ambiguous_2,
    }


def make_csv_bytes(rows: list[list[str]], headers: list[str] | None = None) -> bytes:
    if headers is None:
        headers = CSV_TEMPLATE_HEADERS
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


@pytest.mark.django_db
class TestQuestionImportEngineUnit:
    """Unit tests for the core QuestionImportEngine."""

    def test_csv_template_generator(self):
        csv_str = generate_csv_template()
        assert "question_type" in csv_str
        assert "MCQ" in csv_str
        assert "MULTIPLE_SELECT" in csv_str
        assert "TRUE_FALSE" in csv_str
        assert "ASSERTION_REASON" in csv_str
        assert "MATCH_FOLLOWING" in csv_str
        assert "DESCRIPTIVE" in csv_str
        assert "UPSC_PREVIOUS_YEAR" in csv_str

    def test_empty_csv(self):
        engine = QuestionImportEngine(b"")
        rows = engine.parse_and_validate()
        assert len(rows) == 0
        assert len(engine.structural_errors) > 0
        assert "empty" in engine.structural_errors[0].lower()

    def test_missing_required_headers(self):
        csv_bytes = b"wrong_header1,wrong_header2\nval1,val2"
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert len(engine.structural_errors) > 0
        assert any("Missing required CSV column" in err for err in engine.structural_errors)

    def test_header_alias_normalization(self, taxonomy_tree):
        headers = ["Type", "Question", "Difficulty", "Topic", "Option A", "Option B", "Correct Choice"]
        data_row = ["MCQ", "What is Article 14?", "EASY", "Right to Equality", "Equality before law", "Freedom of speech", "A"]
        csv_bytes = make_csv_bytes([data_row], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert len(rows) == 1
        assert rows[0].is_valid is True
        assert rows[0].question_type == QuestionType.MCQ
        assert rows[0].text == "What is Article 14?"
        assert rows[0].difficulty == Difficulty.EASY
        assert rows[0].topic == taxonomy_tree["topic1"]

    def test_utf8_bom_decoding(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        data_row = ["MCQ", "BOM test question?", "EASY", "Right to Equality", "Choice 1", "Choice 2", "A"]
        raw_csv = make_csv_bytes([data_row], headers=headers)
        bom_csv = b"\xef\xbb\xbf" + raw_csv  # UTF-8 BOM
        engine = QuestionImportEngine(bom_csv)
        rows = engine.parse_and_validate()
        assert len(rows) == 1
        assert rows[0].is_valid is True
        assert rows[0].question_type == QuestionType.MCQ

    def test_exceeding_max_rows(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        rows = [["MCQ", f"Question {i}", "MEDIUM", "Right to Equality", "A", "B", "A"] for i in range(MAX_IMPORT_ROWS + 5)]
        csv_bytes = make_csv_bytes(rows, headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert any("exceeds maximum batch limit" in err for err in engine.structural_errors)

    def test_taxonomy_resolution_by_id(self, taxonomy_tree):
        topic = taxonomy_tree["topic1"]
        headers = ["question_type", "text", "difficulty", "topic_id", "choice_a", "choice_b", "correct_answer"]
        row_data = ["MCQ", "Question referencing Topic ID", "MEDIUM", str(topic.id), "Opt 1", "Opt 2", "A"]
        csv_bytes = make_csv_bytes([row_data], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert len(rows) == 1
        assert rows[0].is_valid is True
        assert rows[0].topic == topic

    def test_taxonomy_resolution_unknown_topic(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        row_data = ["MCQ", "Question referencing fake topic", "MEDIUM", "NonExistentTopic123", "Opt 1", "Opt 2", "A"]
        csv_bytes = make_csv_bytes([row_data], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert len(rows) == 1
        assert rows[0].is_valid is False
        assert any("was not found" in err.message for err in rows[0].errors)
        # Ensure no taxonomy record was silently created
        assert not Topic.objects.filter(name="NonExistentTopic123").exists()

    def test_taxonomy_ambiguity_handling(self, taxonomy_tree):
        # Ambiguous topic without chapter specified
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        row_data = ["MCQ", "Ambiguous question", "MEDIUM", "Common Topics", "Opt 1", "Opt 2", "A"]
        csv_bytes = make_csv_bytes([row_data], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert len(rows) == 1
        assert rows[0].is_valid is False
        assert any("is ambiguous" in err.message for err in rows[0].errors)

        # Disambiguated by chapter
        headers_disambig = ["question_type", "text", "difficulty", "topic_name", "chapter_name", "choice_a", "choice_b", "correct_answer"]
        row_disambig = ["MCQ", "Disambiguated question", "MEDIUM", "Common Topics", "Fundamental Rights", "Opt 1", "Opt 2", "A"]
        csv_bytes2 = make_csv_bytes([row_disambig], headers=headers_disambig)
        engine2 = QuestionImportEngine(csv_bytes2)
        rows2 = engine2.parse_and_validate()
        assert len(rows2) == 1
        assert rows2[0].is_valid is True
        assert rows2[0].topic == taxonomy_tree["topic_ambiguous_1"]

    def test_validate_all_six_question_types(self, taxonomy_tree):
        headers = [
            "question_type", "text", "difficulty", "topic_name",
            "choice_a", "choice_b", "choice_c", "choice_d", "correct_answer",
            "assertion", "reason", "correct_relationship",
            "match_left_items", "match_right_items", "match_pairs",
            "marks", "expected_answer", "source_type", "source_year"
        ]
        test_rows = [
            # 1. MCQ
            ["MCQ", "MCQ stem", "MEDIUM", "Right to Equality", "Opt A", "Opt B", "Opt C", "Opt D", "A", "", "", "", "", "", "", "", "", "UPSC_PREVIOUS_YEAR", "2020"],
            # 2. MULTIPLE_SELECT
            ["MULTIPLE_SELECT", "MS stem", "HARD", "Right to Equality", "Opt A", "Opt B", "Opt C", "Opt D", "A, C", "", "", "", "", "", "", "", "", "ORIGINAL", ""],
            # 3. TRUE_FALSE
            ["TRUE_FALSE", "TF stem", "EASY", "Right to Equality", "", "", "", "", "TRUE", "", "", "", "", "", "", "", "", "ORIGINAL", ""],
            # 4. ASSERTION_REASON
            ["ASSERTION_REASON", "AR stem", "HARD", "Right to Equality", "", "", "", "", "", "Assertion text", "Reason text", "A", "", "", "", "", "", "UPSC_PREVIOUS_YEAR", "2018"],
            # 5. MATCH_FOLLOWING
            ["MATCH_FOLLOWING", "MF stem", "MEDIUM", "Right to Equality", "", "", "", "", "", "", "", "", "1. Item 1 | 2. Item 2", "A. Match A | B. Match B", "1:A, 2:B", "", "", "ORIGINAL", ""],
            # 6. DESCRIPTIVE
            ["DESCRIPTIVE", "Descriptive stem", "HARD", "Right to Equality", "", "", "", "", "", "", "", "", "", "", "", "15", "Expected answer key rubric", "UPSC_PREVIOUS_YEAR", "2021"],
        ]
        csv_bytes = make_csv_bytes(test_rows, headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        parsed = engine.parse_and_validate()
        assert len(parsed) == 6
        for row in parsed:
            assert row.is_valid is True, f"Row {row.row_number} ({row.question_type}) failed: {[e.message for e in row.errors]}"

    def test_mcq_invalid_choices(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "correct_answer"]
        row_data = ["MCQ", "Only one choice", "MEDIUM", "Right to Equality", "Opt A", "A"]
        csv_bytes = make_csv_bytes([row_data], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert rows[0].is_valid is False
        assert any("MCQ must contain at least two choices" in err.message for err in rows[0].errors)

    def test_mcq_invalid_correct_answer(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        row_data = ["MCQ", "Wrong answer reference", "MEDIUM", "Right to Equality", "Opt A", "Opt B", "Z"]
        csv_bytes = make_csv_bytes([row_data], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert rows[0].is_valid is False
        assert any("Correct answer does not reference a supplied choice" in err.message for err in rows[0].errors)

    def test_match_following_invalid_pairs(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "match_left_items", "match_right_items", "match_pairs"]
        row_data = ["MATCH_FOLLOWING", "Invalid pairs", "HARD", "Right to Equality", "1. Left 1 | 2. Left 2", "A. Right A | B. Right B", "1:Z, 2:B"]
        csv_bytes = make_csv_bytes([row_data], headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        rows = engine.parse_and_validate()
        assert rows[0].is_valid is False
        assert any("out of range" in err.message for err in rows[0].errors)

    def test_duplicate_detection_against_db(self, taxonomy_tree):
        # Create an existing question in the DB with topic linkage
        existing_text = "What is the basic structure of the Constitution?"
        q = Question.objects.create()
        QuestionVersion.objects.create(
            question=q,
            version_number=1,
            status=QuestionStatus.DRAFT,
            text=existing_text,
            difficulty=Difficulty.MEDIUM,
            source_type=QuestionSourceType.UPSC_PREVIOUS_YEAR,
            external_question_id="UPSC-2015-Q01",
        )
        from apps.question_bank.models import QuestionTopic
        QuestionTopic.objects.create(question=q, topic=taxonomy_tree["topic1"])

        # Row 1 has duplicate external_question_id (STRONG duplicate)
        # Row 2 has identical normalized text stem in same topic, but different external ID (POTENTIAL duplicate)
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer", "source_type", "external_question_id"]
        rows = [
            ["MCQ", "Different text but duplicate ID", "MEDIUM", "Right to Equality", "A", "B", "A", "UPSC_PREVIOUS_YEAR", "UPSC-2015-Q01"],
            ["MCQ", "what is the basic structure of the constitution?", "MEDIUM", "Right to Equality", "A", "B", "A", "ORIGINAL", "DIFF-ID-001"],
        ]
        csv_bytes = make_csv_bytes(rows, headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        parsed = engine.parse_and_validate()
        assert len(parsed) == 2
        # Row 1: Strong duplicate on authoritative provenance signal
        assert parsed[0].is_duplicate is True
        assert parsed[0].duplicate_type == "STRONG"
        assert "external_question_id" in parsed[0].duplicate_reason

        # Row 2: Potential textual match: classified and reported, NOT suppressed
        assert parsed[1].is_duplicate is False
        assert parsed[1].duplicate_type == "POTENTIAL"
        assert "Potential textual similarity" in parsed[1].duplicate_reason

    def test_conservative_normalization_preserves_operators(self, taxonomy_tree):
        # Questions with code/math operators must not be aggressively stripped into collisions
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        rows = [
            ["MCQ", "What is the result of if (x == 1)?", "EASY", "Right to Equality", "Opt A", "Opt B", "A"],
            ["MCQ", "What is the result of if (x != 1)?", "EASY", "Right to Equality", "Opt A", "Opt B", "A"],
        ]
        csv_bytes = make_csv_bytes(rows, headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        parsed = engine.parse_and_validate()
        assert len(parsed) == 2
        assert parsed[0].is_duplicate is False
        assert parsed[1].is_duplicate is False

    def test_taxonomy_lookup_is_bounded_to_batch(self, taxonomy_tree):
        # Multiple topics exist in taxonomy_tree (topic1, topic2, topic3, topic_ambiguous_1, topic_ambiguous_2)
        # Import only references topic1
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        rows = [
            ["MCQ", "Question referencing only topic 1", "EASY", "Right to Equality", "Opt A", "Opt B", "A"],
        ]
        csv_bytes = make_csv_bytes(rows, headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        engine.parse_and_validate()

        # Engine cache must contain ONLY topic1, NOT all topics from the entire taxonomy
        assert len(engine._topics_cache) == 1
        assert taxonomy_tree["topic1"].id in engine._topics_cache
        assert taxonomy_tree["topic2"].id not in engine._topics_cache
        assert taxonomy_tree["topic3"].id not in engine._topics_cache

    def test_duplicate_detection_within_batch(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer", "external_question_id"]
        rows = [
            ["MCQ", "Batch duplicate question stem", "MEDIUM", "Right to Equality", "A", "B", "A", "ID-001"],
            ["MCQ", "Batch duplicate question stem", "MEDIUM", "Right to Equality", "A", "B", "A", "ID-002"],
        ]
        csv_bytes = make_csv_bytes(rows, headers=headers)
        engine = QuestionImportEngine(csv_bytes)
        parsed = engine.parse_and_validate()
        assert len(parsed) == 2
        assert parsed[0].is_duplicate is False
        assert parsed[1].is_duplicate is True
        assert "within this CSV batch" in parsed[1].duplicate_reason


@pytest.mark.django_db
class TestQuestionImportExecutionAndLifecycle:
    """Tests for execute_question_import, transaction semantics, and DRAFT lifecycle."""

    def test_successful_execution_creates_draft_questions(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer", "source_type", "source_year", "external_question_id"]
        rows = [
            ["MCQ", "Import Question 1", "EASY", "Right to Equality", "Opt A", "Opt B", "A", "UPSC_PREVIOUS_YEAR", "2020", "IMP-001"],
            ["MCQ", "Import Question 2", "MEDIUM", "Right to Equality", "Opt 1", "Opt 2", "B", "ORIGINAL", "", "IMP-002"],
        ]
        csv_bytes = make_csv_bytes(rows, headers=headers)

        result = execute_question_import(csv_bytes, skip_duplicates=False)
        assert result["total_rows"] == 2
        assert result["imported_rows"] == 2
        assert result["skipped_rows"] == 0
        assert result["failed_rows"] == 0
        assert len(result["created_question_ids"]) == 2

        # Verify Question Bank state
        created_questions = Question.objects.filter(id__in=result["created_question_ids"])
        assert created_questions.count() == 2

        for q in created_questions:
            assert q.latest_version is not None
            assert q.latest_version.status == QuestionStatus.DRAFT
            assert q.latest_version.version_number == 1
            assert q.question_topics.filter(topic=taxonomy_tree["topic1"]).exists()

        # Check provenance
        q1 = Question.objects.get(versions__external_question_id="IMP-001")
        assert q1.latest_version.source_type == QuestionSourceType.UPSC_PREVIOUS_YEAR
        assert q1.latest_version.source_year == 2020

        q2 = Question.objects.get(versions__external_question_id="IMP-002")
        assert q2.latest_version.source_type == QuestionSourceType.ORIGINAL
        assert q2.latest_version.source_year is None

    def test_option_a_transaction_rollback_on_invalid_row(self, taxonomy_tree):
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        rows = [
            ["MCQ", "Valid Question Before Error", "EASY", "Right to Equality", "Opt A", "Opt B", "A"],
            ["MCQ", "Invalid Question With Bad Topic", "EASY", "NonExistentTopic", "Opt A", "Opt B", "A"],
        ]
        csv_bytes = make_csv_bytes(rows, headers=headers)

        initial_count = Question.objects.count()

        with pytest.raises(Exception):
            execute_question_import(csv_bytes, skip_duplicates=False)

        # Entire batch must be rolled back (Option A)
        assert Question.objects.count() == initial_count

    def test_skip_duplicates_behavior(self, taxonomy_tree):
        # Create existing question
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer", "external_question_id"]
        initial_row = [["MCQ", "Existing Unique Question", "MEDIUM", "Right to Equality", "Opt A", "Opt B", "A", "EXT-EXISTING-1"]]
        execute_question_import(make_csv_bytes(initial_row, headers=headers))

        # Upload batch with 1 duplicate and 1 new question
        batch_rows = [
            ["MCQ", "Existing Unique Question", "MEDIUM", "Right to Equality", "Opt A", "Opt B", "A", "EXT-EXISTING-1"],
            ["MCQ", "Brand New Question", "EASY", "Right to Equality", "Opt A", "Opt B", "A", "EXT-NEW-2"],
        ]
        csv_bytes = make_csv_bytes(batch_rows, headers=headers)

        # If skip_duplicates is True, duplicate should be skipped and new one imported
        result = execute_question_import(csv_bytes, skip_duplicates=True)
        assert result["total_rows"] == 2
        assert result["imported_rows"] == 1
        assert result["skipped_rows"] == 1
        assert Question.objects.filter(versions__external_question_id="EXT-NEW-2").exists()


@pytest.mark.django_db
class TestQuestionImportAPIEndpoints:
    """API endpoint tests for preview, execute, and template download."""

    def test_template_download_unauthenticated_rejected(self, api_client):
        url = "/api/v1/question-bank/imports/template/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_template_download_student_forbidden(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        url = "/api/v1/question-bank/imports/template/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_template_download_superadmin_success(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        url = "/api/v1/question-bank/imports/template/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"].startswith("text/csv")
        assert "attachment; filename=\"nexora_upsc_question_import_template.csv\"" in response["Content-Disposition"]
        content = response.content.decode("utf-8")
        assert "question_type" in content
        assert "UPSC_PREVIOUS_YEAR" in content

    def test_preview_endpoint_success(self, api_client, superadmin_user, taxonomy_tree):
        api_client.force_authenticate(user=superadmin_user)
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        rows = [
            ["MCQ", "Valid Preview Question 1", "EASY", "Right to Equality", "Opt A", "Opt B", "A"],
            ["MCQ", "Invalid Preview Question 2", "EASY", "FakeTopic", "Opt A", "Opt B", "A"],
        ]
        csv_file = SimpleUploadedFile("import.csv", make_csv_bytes(rows, headers=headers), content_type="text/csv")

        url = "/api/v1/question-bank/imports/preview/"
        response = api_client.post(url, {"file": csv_file}, format="multipart")

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["row_number"] == 3  # row 1 is header, row 2 is valid, row 3 is invalid
        assert "was not found" in data["errors"][0]["message"]
        assert len(data["rows"]) == 2

    def test_preview_endpoint_file_too_large(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        # Create dummy file > 5MB
        oversized_content = b"a" * (5 * 1024 * 1024 + 100)
        csv_file = SimpleUploadedFile("large.csv", oversized_content, content_type="text/csv")

        url = "/api/v1/question-bank/imports/preview/"
        response = api_client.post(url, {"file": csv_file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds" in str(response.data).lower()

    def test_preview_endpoint_non_csv_rejected(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        pdf_file = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 dummy", content_type="application/pdf")

        url = "/api/v1/question-bank/imports/preview/"
        response = api_client.post(url, {"file": pdf_file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "csv" in str(response.data).lower()

    def test_preview_endpoint_binary_named_csv_rejected(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        # Binary content with null bytes named .csv and MIME text/csv
        binary_payload = b"\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x03\x00"
        csv_file = SimpleUploadedFile("payload.csv", binary_payload, content_type="text/csv")

        url = "/api/v1/question-bank/imports/preview/"
        response = api_client.post(url, {"file": csv_file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "binary" in str(response.data).lower() or "null" in str(response.data).lower()

    def test_preview_endpoint_invalid_utf8_named_csv_rejected(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        # Non-decodable UTF-8 bytes without null bytes
        invalid_utf8 = b"question_type,text\nMCQ,\xff\xfe\xfa\xfb invalid bytes"
        csv_file = SimpleUploadedFile("invalid_encoding.csv", invalid_utf8, content_type="text/csv")

        url = "/api/v1/question-bank/imports/preview/"
        response = api_client.post(url, {"file": csv_file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "decoded" in str(response.data).lower() or "utf-8" in str(response.data).lower()

    def test_execute_endpoint_success(self, api_client, superadmin_user, taxonomy_tree):
        api_client.force_authenticate(user=superadmin_user)
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer", "source_type", "source_year"]
        rows = [
            ["MCQ", "Execute Test Question 1", "EASY", "Right to Equality", "Opt A", "Opt B", "A", "UPSC_PREVIOUS_YEAR", "2021"],
            ["MCQ", "Execute Test Question 2", "MEDIUM", "Right to Equality", "Opt 1", "Opt 2", "B", "ORIGINAL", ""],
        ]
        csv_file = SimpleUploadedFile("execute.csv", make_csv_bytes(rows, headers=headers), content_type="text/csv")

        url = "/api/v1/question-bank/imports/execute/"
        response = api_client.post(url, {"file": csv_file, "skip_duplicates": False}, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert data["total_rows"] == 2
        assert data["imported_rows"] == 2
        assert data["skipped_rows"] == 0
        assert data["failed_rows"] == 0
        assert len(data["created_question_ids"]) == 2

        # Verify questions exist in DB as DRAFT
        for qid in data["created_question_ids"]:
            q = Question.objects.get(id=qid)
            assert q.latest_version.status == QuestionStatus.DRAFT

    def test_execute_endpoint_validation_failure_rolls_back(self, api_client, superadmin_user, taxonomy_tree):
        api_client.force_authenticate(user=superadmin_user)
        headers = ["question_type", "text", "difficulty", "topic_name", "choice_a", "choice_b", "correct_answer"]
        rows = [
            ["MCQ", "Valid In Batch Before Error", "EASY", "Right to Equality", "Opt A", "Opt B", "A"],
            ["MCQ", "Invalid In Batch", "EASY", "NonExistentTopic", "Opt A", "Opt B", "A"],
        ]
        csv_file = SimpleUploadedFile("execute_fail.csv", make_csv_bytes(rows, headers=headers), content_type="text/csv")

        initial_count = Question.objects.count()

        url = "/api/v1/question-bank/imports/execute/"
        response = api_client.post(url, {"file": csv_file, "skip_duplicates": False}, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # No questions created
        assert Question.objects.count() == initial_count
