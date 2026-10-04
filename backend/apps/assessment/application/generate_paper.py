from uuid import UUID
from django.db import transaction

from apps.assessment.exceptions import (
    AssessmentEmptyError,
    AssessmentNotFoundError,
    AssessmentNotPublishedError,
    InsufficientQuestionsError,
)
from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentStatus,
    PaperStatus,
)
from apps.assessment.ports.question_bank import QuestionBankCandidatePort


@transaction.atomic
def generate_paper(
    assessment_id: UUID,
    question_bank_port: QuestionBankCandidatePort,
) -> AssessmentPaper:
    """
    Application use case for generating an immutable AssessmentPaper from an Assessment definition.
    Workflow:
    1. Locks and validates Assessment is PUBLISHED.
    2. Loads sections and selection rules in deterministic order.
    3. Resolves published candidate questions via QuestionBankCandidatePort.
    4. Filters and deduplicates candidates by stable Question.id across all rules.
    5. Validates sufficient candidates exist for every rule (aborts entire transaction if insufficient).
    6. Pins exact QuestionVersion IDs and captures timing/marking snapshots.
    7. Creates AssessmentPaper and AssessmentPaperItem records atomically.
    """
    assessment = (
        Assessment.objects.select_for_update()
        .filter(id=assessment_id)
        .first()
    )
    if not assessment:
        raise AssessmentNotFoundError("Assessment not found.")

    if assessment.status != AssessmentStatus.PUBLISHED:
        raise AssessmentNotPublishedError(
            f"Cannot generate paper: assessment is in '{assessment.status}' status (must be PUBLISHED)."
        )

    rules = list(
        assessment.selection_rules.select_related("assessment_section")
        .order_by("position", "created_at")
    )
    if not rules:
        raise AssessmentEmptyError("Assessment has no selection rules configured.")

    selected_question_ids: set[UUID] = set()
    items_to_create: list[AssessmentPaperItem] = []
    presentation_order = 1

    # First instantiate the paper record to associate items
    paper = AssessmentPaper.objects.create(
        assessment=assessment,
        status=PaperStatus.GENERATED,
        duration_seconds=assessment.duration_seconds,
        marks_per_question=assessment.marks_per_question,
        penalty_per_question=assessment.penalty_per_question,
    )

    for rule in rules:
        candidates = question_bank_port.get_published_candidates(
            scope_type=rule.scope_type,
            scope_id=rule.scope_id,
            question_type=rule.question_type,
            difficulty=rule.difficulty,
        )

        # Deduplicate against already selected questions in previous rules
        eligible = [
            c for c in candidates
            if c.question_id not in selected_question_ids
        ]

        if len(eligible) < rule.question_count:
            raise InsufficientQuestionsError(
                f"Insufficient eligible questions for rule {rule.position} "
                f"(scope {rule.scope_type}:{rule.scope_id}): "
                f"required {rule.question_count}, found {len(eligible)} eligible."
            )

        selected_candidates = eligible[:rule.question_count]

        for cand in selected_candidates:
            selected_question_ids.add(cand.question_id)
            items_to_create.append(
                AssessmentPaperItem(
                    paper=paper,
                    question_id=cand.question_id,
                    question_version_id=cand.question_version_id,
                    assessment_section=rule.assessment_section,
                    presentation_order=presentation_order,
                    allocated_marks=assessment.marks_per_question,
                    allocated_penalty=assessment.penalty_per_question,
                )
            )
            presentation_order += 1

    AssessmentPaperItem.objects.bulk_create(items_to_create)
    return paper
