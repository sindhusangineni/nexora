import uuid
from django.db import models


class AttemptResponseChoice(models.Model):
    """
    Selected choices for MCQ / MULTIPLE_SELECT responses.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_response = models.ForeignKey(
        "attempts.AttemptResponse",
        on_delete=models.CASCADE,
        related_name="choices",
    )
    choice_id = models.UUIDField()

    class Meta:
        db_table = "attempts_attempt_response_choice"
        verbose_name = "attempt response choice"
        verbose_name_plural = "attempt response choices"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt_response", "choice_id"],
                name="uq_attempt_response_choice_response_choice",
            ),
        ]

    def __str__(self) -> str:
        return f"Choice {self.choice_id} on Response {self.attempt_response_id}"
