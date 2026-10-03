from uuid import UUID
from django.apps import apps

from apps.assessment.ports.question_bank import (
    QuestionBankCandidatePort,
    QuestionCandidateDTO,
)


class DatabaseQuestionBankCandidateAdapter(QuestionBankCandidatePort):
    """
    Production candidate query adapter executing queries across
    Question Bank and Learning schemas using dynamic app model resolution.
    Avoids static cross-module model imports and preserves strict Clean Architecture decoupling.
    """

    def get_published_candidates(
        self,
        scope_type: str,
        scope_id: UUID,
        question_type: str | None = None,
        difficulty: str | None = None,
    ) -> list[QuestionCandidateDTO]:
        QuestionTopic = apps.get_model("question_bank", "QuestionTopic")
        QuestionVersion = apps.get_model("question_bank", "QuestionVersion")

        scope_type_upper = scope_type.upper()
        topic_filter = {}

        if scope_type_upper == "TOPIC":
            topic_filter["topic_id"] = scope_id
        elif scope_type_upper == "CHAPTER":
            topic_filter["topic__chapter_id"] = scope_id
        elif scope_type_upper == "SUBJECT":
            topic_filter["topic__chapter__subject_id"] = scope_id
        elif scope_type_upper == "DOMAIN":
            topic_filter["topic__chapter__subject__domain_id"] = scope_id
        else:
            return []

        matching_q_ids = (
            QuestionTopic.objects.filter(**topic_filter)
            .values_list("question_id", flat=True)
            .distinct()
        )

        version_qs = (
            QuestionVersion.objects.filter(
                question_id__in=matching_q_ids,
                status="PUBLISHED",
            )
            .select_related("question")
            .order_by("question__created_at", "question_id")
        )

        if question_type:
            version_qs = version_qs.filter(question_type=question_type)
        if difficulty:
            version_qs = version_qs.filter(difficulty=difficulty)

        candidates: list[QuestionCandidateDTO] = []
        for qv in version_qs:
            candidates.append(
                QuestionCandidateDTO(
                    question_id=qv.question_id,
                    question_version_id=qv.id,
                    question_type=qv.question_type,
                    difficulty=qv.difficulty,
                )
            )
        return candidates
