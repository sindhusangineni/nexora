from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class ObjectiveAnswerKeyDTO:
    question_version_id: UUID
    question_type: str
    correct_choice_ids: set[UUID]
    correct_boolean: bool | None
    correct_assertion_reason: str | None
    correct_match_pairs: dict[UUID, UUID]


@dataclass(frozen=True)
class QuestionReviewSnapshotDTO:
    question_version_id: UUID
    question_id: UUID
    question_type: str
    text: str
    explanation: str
    taxonomy: dict[str, str] | None
    choices: list[dict[str, Any]]
    true_false_answer: bool | None
    assertion_reason: dict[str, Any] | None
    match_following: dict[str, Any] | None
    descriptive: dict[str, Any] | None


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

    def get_question_review_snapshots(
        self,
        pinned_version_ids: list[UUID],
    ) -> dict[UUID, QuestionReviewSnapshotDTO]:
        """
        Fetch complete review snapshots (text, choices, content, taxonomy, solutions)
        for pinned version identities. Operates without cross-module FKs.
        """
        ...

