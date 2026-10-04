from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class PaperChoiceDTO:
    choice_id: UUID
    choice_text: str
    presented_position: int


@dataclass(frozen=True)
class PaperMatchPairDTO:
    left_item_id: UUID
    left_text: str
    right_item_id: UUID
    right_text: str


@dataclass(frozen=True)
class PaperItemDTO:
    paper_item_id: UUID
    question_id: UUID
    question_version_id: UUID
    question_type: str
    assessment_section_id: UUID | None
    section_order: int
    presentation_order: int
    allocated_marks: Decimal
    allocated_penalty: Decimal
    choices: list[PaperChoiceDTO] = field(default_factory=list)
    match_pairs: list[PaperMatchPairDTO] = field(default_factory=list)


@dataclass(frozen=True)
class DeliveryPayloadDTO:
    assessment_paper_id: UUID
    duration_seconds: int
    is_eligible: bool
    eligibility_error: str | None
    items: list[PaperItemDTO]


class AssessmentPaperPort(Protocol):
    def get_paper_delivery_payload(
        self,
        paper_id: UUID,
        student_id: UUID,
    ) -> DeliveryPayloadDTO:
        """
        Fetch delivery payload and verify eligibility for an assessment paper.
        Operates without ORM coupling.
        """
        ...
