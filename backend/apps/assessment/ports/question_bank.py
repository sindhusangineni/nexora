from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class QuestionCandidateDTO:
    """
    Candidate question representation for assessment paper generation.
    Carries stable question identity and pinned published version identity.
    """

    question_id: UUID
    question_version_id: UUID
    question_type: str
    difficulty: str


class QuestionBankCandidatePort(Protocol):
    """
    Port contract for querying published question candidates from Question Bank.
    Operates without ORM model coupling.
    """

    def get_published_candidates(
        self,
        scope_type: str,
        scope_id: UUID,
        question_type: str | None = None,
        difficulty: str | None = None,
    ) -> list[QuestionCandidateDTO]:
        """
        Query eligible published questions within the given taxonomy scope,
        applying optional question_type and difficulty filters.
        """
        ...
