from decimal import Decimal
from typing import Protocol


class ScoringPolicy(Protocol):
    """Protocol defining the interface for score calculation policies."""

    policy_version: str

    def calculate_score(
        self,
        raw_score: Decimal,
        maximum_score: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate final score and percentage from raw score and maximum score.
        Returns: (score, percentage) rounded to 2 decimal places.
        """
        ...


class UnrestrictedScoringPolicy:
    """
    Unrestricted policy: retains negative raw scores and computes unrestricted percentage.
    """

    policy_version = "UNRESTRICTED_v1"

    def calculate_score(
        self,
        raw_score: Decimal,
        maximum_score: Decimal,
    ) -> tuple[Decimal, Decimal]:
        score = raw_score.quantize(Decimal("0.01"))
        if maximum_score == Decimal("0.00") or maximum_score == Decimal("0"):
            percentage = Decimal("0.00")
        else:
            percentage = ((score / maximum_score) * Decimal("100")).quantize(Decimal("0.01"))
        return score, percentage


class ZeroFloorTotalScoringPolicy:
    """
    Zero-floor total policy: floors the total score at zero.
    """

    policy_version = "ZERO_FLOOR_TOTAL_v1"

    def calculate_score(
        self,
        raw_score: Decimal,
        maximum_score: Decimal,
    ) -> tuple[Decimal, Decimal]:
        score = max(Decimal("0.00"), raw_score).quantize(Decimal("0.01"))
        if maximum_score == Decimal("0.00") or maximum_score == Decimal("0"):
            percentage = Decimal("0.00")
        else:
            percentage = ((score / maximum_score) * Decimal("100")).quantize(Decimal("0.01"))
        return score, percentage


class ZeroFloorSectionScoringPolicy:
    """
    Zero-floor section policy: floors section scores at zero before summation.
    For overall scoring calculation, behaves identically to zero-floor total.
    """

    policy_version = "ZERO_FLOOR_SECTION_v1"

    def calculate_score(
        self,
        raw_score: Decimal,
        maximum_score: Decimal,
    ) -> tuple[Decimal, Decimal]:
        score = max(Decimal("0.00"), raw_score).quantize(Decimal("0.01"))
        if maximum_score == Decimal("0.00") or maximum_score == Decimal("0"):
            percentage = Decimal("0.00")
        else:
            percentage = ((score / maximum_score) * Decimal("100")).quantize(Decimal("0.01"))
        return score, percentage


def get_scoring_policy(policy_name: str) -> ScoringPolicy:
    """
    Resolves the appropriate ScoringPolicy implementation matching an Attempt's
    configured score_floor_policy.
    """
    from apps.attempts.models.enums import ScoreFloorPolicy

    if policy_name == ScoreFloorPolicy.ZERO_FLOOR_TOTAL:
        return ZeroFloorTotalScoringPolicy()
    elif policy_name == ScoreFloorPolicy.ZERO_FLOOR_SECTION:
        return ZeroFloorSectionScoringPolicy()
    elif policy_name == ScoreFloorPolicy.UNRESTRICTED:
        return UnrestrictedScoringPolicy()
    raise ValueError(f"Unknown scoring policy: {policy_name}")

