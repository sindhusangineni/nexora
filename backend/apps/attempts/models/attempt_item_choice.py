import uuid
from django.core.exceptions import ValidationError
from django.db import models


class AttemptItemChoice(models.Model):
    """
    Materialized presentation order of choices for MCQ and MULTIPLE_SELECT questions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_item = models.ForeignKey(
        "attempts.AttemptItem",
        on_delete=models.CASCADE,
        related_name="choices",
    )
    choice_id = models.UUIDField()
    presented_position = models.PositiveIntegerField()

    class Meta:
        db_table = "attempts_attempt_item_choice"
        verbose_name = "attempt item choice"
        verbose_name_plural = "attempt item choices"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt_item", "presented_position"],
                name="uq_attempt_item_choice_item_presented_position",
            ),
            models.UniqueConstraint(
                fields=["attempt_item", "choice_id"],
                name="uq_attempt_item_choice_item_choice_id",
            ),
            models.CheckConstraint(
                condition=models.Q(presented_position__gte=1),
                name="chk_attempt_item_choice_presented_position_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["attempt_item", "presented_position"], name="idx_attempt_choice_pos"),
        ]

    def __str__(self) -> str:
        return f"Position {self.presented_position} on Item {self.attempt_item_id} (Choice {self.choice_id})"

    def clean(self):
        super().clean()
        if self.presented_position is not None and self.presented_position < 1:
            raise ValidationError({"presented_position": "presented_position must be a positive integer (>= 1)."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
