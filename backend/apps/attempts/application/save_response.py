from datetime import datetime
from uuid import UUID

from django.db import transaction

from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptExpired,
    AttemptNotFoundError,
    InvalidAttemptStateError,
    InvalidResponseError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptItem,
    AttemptResponse,
    AttemptResponseChoice,
    AttemptResponseMatch,
    AttemptStatus,
)
from apps.attempts.ports.question_bank import QuestionBankPort
from apps.attempts.services.response_validation import (
    validate_assertion_reason_response,
    validate_descriptive_response,
    validate_match_following_response,
    validate_mcq_response,
    validate_multiple_select_response,
    validate_true_false_response,
)
from apps.attempts.services.scoring import ScoringPolicy
from apps.attempts.services.submission import execute_timeout_submission
from apps.attempts.services.timing import get_authoritative_now, is_attempt_expired


def save_response(
    *,
    attempt_id: UUID,
    attempt_item_id: UUID,
    authorization: AuthorizationContext,
    response_data: dict,
    question_bank_port: QuestionBankPort | None = None,
    scoring_policy: ScoringPolicy | None = None,
    now: datetime | None = None,
) -> AttemptResponse:
    """
    Use Case: Save or update student answer on an AttemptItem.

    Transaction & Concurrency Guarantees:
    1. Locks the Attempt row (select_for_update) inside an atomic transaction.
    2. Validates student ownership and IN_PROGRESS lifecycle state.
    3. If expired (now >= expires_at):
       - Rejects response mutation.
       - Executes timeout auto-submission within the atomic block.
       - Commits transaction durably to PostgreSQL.
       - Raises AttemptExpired (HTTP 409) post-commit.
    4. If active (now < expires_at):
       - Validates response payload against pinned Attempt snapshot.
       - Replaces response state and child records atomically.
       - Commits transaction and returns the updated AttemptResponse.
    """
    current_now = now if now is not None else get_authoritative_now()
    is_expired = False
    saved_response: AttemptResponse | None = None

    with transaction.atomic():
        attempt = (
            Attempt.objects.select_for_update()
            .filter(id=attempt_id)
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        if not authorization.is_student or authorization.actor_id != attempt.student_id:
            raise AttemptAuthorizationError("Students may only mutate their own test attempts.")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStateError(
                f"Cannot save response on attempt with status '{attempt.status}'."
            )

        attempt_item = (
            AttemptItem.objects.filter(id=attempt_item_id, attempt_id=attempt.id)
            .first()
        )
        if attempt_item is None:
            raise AttemptNotFoundError(
                f"AttemptItem '{attempt_item_id}' not found on attempt '{attempt_id}'."
            )

        if is_attempt_expired(attempt.expires_at, current_now):
            # Timed out! Reject mutation and commit timeout submission
            if scoring_policy is None:
                raise ValueError("A ScoringPolicy must be explicitly provided for timeout submission.")
            if question_bank_port is None:
                from apps.attempts.adapters.question_bank import DatabaseQuestionBankAnswerKeyAdapter
                question_bank_port = DatabaseQuestionBankAnswerKeyAdapter()
            execute_timeout_submission(
                attempt=attempt,
                now=current_now,
                scoring_policy=scoring_policy,
                question_bank_port=question_bank_port,
            )
            is_expired = True
        else:
            # Active attempt: apply response replacement
            resp = AttemptResponse.objects.select_for_update().get(attempt_item=attempt_item)
            q_type = response_data.get("question_type")

            # Reset child rows and scalar fields
            resp.boolean_response = None
            resp.assertion_reason_response = None
            resp.text_response = None
            resp.choices.all().delete()
            resp.matches.all().delete()

            if q_type == "MCQ" or ("choice_id" in response_data):
                choice_ids = [response_data["choice_id"]] if "choice_id" in response_data else response_data.get("selected_choice_ids")
                valid_choice_id = validate_mcq_response(attempt_item, choice_ids)
                AttemptResponseChoice.objects.create(attempt_response=resp, choice_id=valid_choice_id)
            elif q_type == "MULTIPLE_SELECT" or ("selected_choice_ids" in response_data):
                choice_ids = response_data.get("selected_choice_ids")
                valid_choice_ids = validate_multiple_select_response(attempt_item, choice_ids)
                for cid in valid_choice_ids:
                    AttemptResponseChoice.objects.create(attempt_response=resp, choice_id=cid)
            elif q_type == "TRUE_FALSE" or ("boolean_response" in response_data):
                bool_val = validate_true_false_response(response_data.get("boolean_response"))
                resp.boolean_response = bool_val
            elif q_type == "ASSERTION_REASON" or ("assertion_reason_response" in response_data):
                ar_val = validate_assertion_reason_response(response_data.get("assertion_reason_response"))
                resp.assertion_reason_response = ar_val
            elif q_type == "MATCH_FOLLOWING" or ("match_pairs" in response_data):
                valid_pairs = validate_match_following_response(
                    response_data.get("match_pairs"),
                    expected_left_ids=response_data.get("expected_left_ids"),
                    expected_right_ids=response_data.get("expected_right_ids"),
                )
                for left_id, right_id in valid_pairs:
                    AttemptResponseMatch.objects.create(
                        attempt_response=resp,
                        left_item_id=left_id,
                        right_item_id=right_id,
                    )
            elif q_type == "DESCRIPTIVE" or ("text_response" in response_data):
                text_val = validate_descriptive_response(
                    response_data.get("text_response"),
                    max_length=response_data.get("max_length"),
                )
                resp.text_response = text_val
            else:
                raise InvalidResponseError("No recognized question response payload provided.")

            resp.answer_state = AnswerState.ANSWERED
            resp.save()
            saved_response = resp

    # Transaction committed durably before raising AttemptExpired
    if is_expired:
        raise AttemptExpired("Attempt has expired and has been submitted.")

    return saved_response  # type: ignore[return-value]
