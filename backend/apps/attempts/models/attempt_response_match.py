import uuid
from django.db import models


class AttemptResponseMatch(models.Model):
    """
    Student's selected matching pairs for MATCH_FOLLOWING responses.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_response = models.ForeignKey(
        "attempts.AttemptResponse",
        on_delete=models.CASCADE,
        related_name="matches",
    )
    left_item_id = models.UUIDField()
    right_item_id = models.UUIDField()

    class Meta:
        db_table = "attempts_attempt_response_match"
        verbose_name = "attempt response match"
        verbose_name_plural = "attempt response matches"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt_response", "left_item_id"],
                name="uq_attempt_response_match_response_left",
            ),
            models.UniqueConstraint(
                fields=["attempt_response", "right_item_id"],
                name="uq_attempt_response_match_response_right",
            ),
        ]

    def __str__(self) -> str:
        return f"Match ({self.left_item_id} -> {self.right_item_id}) on Response {self.attempt_response_id}"
