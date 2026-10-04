import uuid
from django.db import models

from apps.attempts.models.enums import AnswerState, AssertionReasonResponse


class AttemptResponse(models.Model):
    """
    Pre-allocated 1:1 response container for an AttemptItem.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_item = models.OneToOneField(
        "attempts.AttemptItem",
        on_delete=models.CASCADE,
        related_name="response",
    )
    answer_state = models.CharField(
        max_length=16,
        choices=AnswerState.choices,
        default=AnswerState.UNANSWERED,
    )
    boolean_response = models.BooleanField(null=True, blank=True)
    assertion_reason_response = models.CharField(
        max_length=64,
        choices=AssertionReasonResponse.choices,
        null=True,
        blank=True,
    )
    text_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attempts_attempt_response"
        verbose_name = "attempt response"
        verbose_name_plural = "attempt responses"

    def __str__(self) -> str:
        return f"Response for Item {self.attempt_item_id} [{self.answer_state}]"
