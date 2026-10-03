from typing import Any
from uuid import UUID

from apps.attempts.exceptions import InvalidResponseError
from apps.attempts.models import AttemptItem
from apps.attempts.models.enums import AssertionReasonResponse


def validate_mcq_response(
    attempt_item: AttemptItem,
    choice_ids: list[UUID] | None,
) -> UUID:
    """Validate MCQ response: exactly one choice belonging to the pinned AttemptItemChoices."""
    if not choice_ids or len(choice_ids) != 1:
        raise InvalidResponseError("MCQ requires exactly one selected choice.")

    selected_choice_id = choice_ids[0]
    valid_choice_ids = set(attempt_item.choices.values_list("choice_id", flat=True))

    if selected_choice_id not in valid_choice_ids:
        raise InvalidResponseError("Selected choice does not belong to this item.")

    return selected_choice_id


def validate_multiple_select_response(
    attempt_item: AttemptItem,
    choice_ids: list[UUID] | None,
) -> list[UUID]:
    """Validate Multiple Select response: at least one choice, unique, belonging to pinned choices."""
    if not choice_ids or len(choice_ids) < 1:
        raise InvalidResponseError("Multiple select requires at least one selected choice.")

    if len(choice_ids) != len(set(choice_ids)):
        raise InvalidResponseError("Duplicate choices selected.")

    valid_choice_ids = set(attempt_item.choices.values_list("choice_id", flat=True))
    for choice_id in choice_ids:
        if choice_id not in valid_choice_ids:
            raise InvalidResponseError(f"Selected choice {choice_id} does not belong to this item.")

    return choice_ids


def validate_true_false_response(
    boolean_response: Any,
) -> bool:
    """Validate True/False response: must be a strict boolean."""
    if not isinstance(boolean_response, bool):
        raise InvalidResponseError("True/False requires a valid boolean response.")
    return boolean_response


def validate_assertion_reason_response(
    assertion_reason_response: Any,
) -> str:
    """Validate Assertion/Reason response: must be one of the approved enum values."""
    if not isinstance(assertion_reason_response, str) or assertion_reason_response not in AssertionReasonResponse.values:
        raise InvalidResponseError(
            f"Invalid assertion-reason response '{assertion_reason_response}'."
        )
    return assertion_reason_response


def validate_match_following_response(
    match_pairs: list[dict[str, Any]] | list[tuple[UUID, UUID]] | dict[UUID, UUID] | None,
    expected_left_ids: set[UUID] | None = None,
    expected_right_ids: set[UUID] | None = None,
) -> list[tuple[UUID, UUID]]:
    """
    Validate Match Following response:
    - Must be a complete injective mapping against the pinned delivery snapshot.
    - Every left item maps to exactly one right item.
    - No right item may be used more than once.
    - No duplicate mappings.
    - If expected_left_ids / expected_right_ids are provided:
      - All expected left items must be present (complete).
      - All right items must belong to the delivered snapshot.
    """
    if not match_pairs:
        raise InvalidResponseError("Match following response cannot be empty.")

    normalized_pairs: list[tuple[UUID, UUID]] = []
    if isinstance(match_pairs, dict):
        for k, v in match_pairs.items():
            normalized_pairs.append((UUID(str(k)), UUID(str(v))))
    elif isinstance(match_pairs, list):
        for item in match_pairs:
            if isinstance(item, dict):
                left = UUID(str(item.get("left_item_id")))
                right = UUID(str(item.get("right_item_id")))
                normalized_pairs.append((left, right))
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                left = UUID(str(item[0]))
                right = UUID(str(item[1]))
                normalized_pairs.append((left, right))
            else:
                raise InvalidResponseError("Invalid match pair format.")
    else:
        raise InvalidResponseError("Invalid match pairs data structure.")

    left_ids = [p[0] for p in normalized_pairs]
    right_ids = [p[1] for p in normalized_pairs]

    if len(left_ids) != len(set(left_ids)):
        raise InvalidResponseError("Duplicate left item in match following mappings.")

    if len(right_ids) != len(set(right_ids)):
        raise InvalidResponseError("Duplicate right item used in match following (must be injective).")

    if expected_left_ids is not None:
        if set(left_ids) != set(expected_left_ids):
            raise InvalidResponseError(
                "Match following mapping is incomplete: all delivered left items must be mapped."
            )

    if expected_right_ids is not None:
        if not set(right_ids).issubset(set(expected_right_ids)):
            raise InvalidResponseError(
                "Match following contains right items that do not belong to the delivered snapshot."
            )

    return normalized_pairs


def validate_descriptive_response(
    text_response: Any,
    max_length: int | None = None,
) -> str:
    """
    Validate Descriptive response:
    - Must be a non-empty string.
    - Whitespace-only responses are invalid.
    - If a specific bound is supplied by the caller, enforces length <= max_length.
    """
    if not isinstance(text_response, str) or not text_response.strip():
        raise InvalidResponseError("Descriptive response cannot be empty.")

    if max_length is not None and len(text_response) > max_length:
        raise InvalidResponseError(
            f"Descriptive response exceeds maximum allowed length of {max_length} characters."
        )

    return text_response

