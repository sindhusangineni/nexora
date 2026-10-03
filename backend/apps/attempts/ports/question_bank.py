from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ObjectiveAnswerKeyDTO:
    question_version_id: UUID
    question_type: str
    correct_choice_ids: set[UUID]
    correct_boolean: bool | None
    correct_assertion_reason: str | None
    correct_match_pairs: dict[UUID, UUID]


class QuestionBankPort(Protocol):
    def get_objective_answer_keys(
        self,
        pinned_version_ids: list[UUID],
    ) -> dict[UUID, ObjectiveAnswerKeyDTO]:
        """
        Fetch answer keys strictly for pinned version identities.
        Operates without ORM coupling.
        """
        ...
