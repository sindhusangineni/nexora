from decimal import Decimal
from uuid import UUID
from django.apps import apps

from apps.assessment.models import AssessmentPaper
from apps.attempts.ports.assessment import (
    AssessmentPaperPort,
    DeliveryPayloadDTO,
    PaperChoiceDTO,
    PaperItemDTO,
    PaperMatchPairDTO,
)


class AssessmentPaperDeliveryAdapter(AssessmentPaperPort):
    """
    Implements Attempts.AssessmentPaperPort by querying AssessmentPaper and its items.
    Queries question choices and match pairs for pinned versions via dynamic model loading,
    avoiding static model imports and preserving strict Clean Architecture decoupling.
    """

    def get_paper_delivery_payload(
        self,
        paper_id: UUID,
        student_id: UUID,
    ) -> DeliveryPayloadDTO:
        paper = (
            AssessmentPaper.objects.filter(id=paper_id)
            .select_related("assessment")
            .prefetch_related("items__assessment_section")
            .first()
        )
        if not paper:
            return DeliveryPayloadDTO(
                assessment_paper_id=paper_id,
                duration_seconds=0,
                is_eligible=False,
                eligibility_error="Assessment paper not found.",
                items=[],
            )

        items_query = list(paper.items.select_related("assessment_section").order_by("presentation_order"))
        version_ids = [item.question_version_id for item in items_query]

        q_types: dict[UUID, str] = {}
        choices_map: dict[UUID, list[PaperChoiceDTO]] = {v: [] for v in version_ids}
        match_map: dict[UUID, list[PaperMatchPairDTO]] = {v: [] for v in version_ids}

        if version_ids:
            QuestionVersion = apps.get_model("question_bank", "QuestionVersion")
            QuestionVersionChoice = apps.get_model("question_bank", "QuestionVersionChoice")
            MatchFollowingPair = apps.get_model("question_bank", "MatchFollowingPair")

            for qv in QuestionVersion.objects.filter(id__in=version_ids):
                q_types[qv.id] = qv.question_type

            for ch in QuestionVersionChoice.objects.filter(question_version_id__in=version_ids).order_by("position"):
                choices_map.setdefault(ch.question_version_id, []).append(
                    PaperChoiceDTO(
                        choice_id=ch.id,
                        choice_text=ch.text,
                        presented_position=ch.position,
                    )
                )

            for mp in MatchFollowingPair.objects.filter(question_version_id__in=version_ids).select_related("left_item", "right_item"):
                match_map.setdefault(mp.question_version_id, []).append(
                    PaperMatchPairDTO(
                        left_item_id=mp.left_item_id,
                        left_text=mp.left_item.text,
                        right_item_id=mp.right_item_id,
                        right_text=mp.right_item.text,
                    )
                )

        paper_items: list[PaperItemDTO] = []
        for item in items_query:
            v_id = item.question_version_id
            q_type = q_types.get(v_id, "MCQ")
            section_id = item.assessment_section.id if item.assessment_section else None
            section_order = item.assessment_section.position if item.assessment_section else 0

            paper_items.append(
                PaperItemDTO(
                    paper_item_id=item.id,
                    question_id=item.question_id,
                    question_version_id=v_id,
                    question_type=q_type,
                    assessment_section_id=section_id,
                    section_order=section_order,
                    presentation_order=item.presentation_order,
                    allocated_marks=item.allocated_marks,
                    allocated_penalty=item.allocated_penalty,
                    choices=choices_map.get(v_id, []),
                    match_pairs=match_map.get(v_id, []),
                )
            )

        return DeliveryPayloadDTO(
            assessment_paper_id=paper.id,
            duration_seconds=paper.duration_seconds,
            is_eligible=True,
            eligibility_error=None,
            items=paper_items,
        )
