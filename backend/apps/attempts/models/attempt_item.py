import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models


class AttemptItem(models.Model):
    """
    Immutable delivery snapshot of one question in an attempt.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        "attempts.Attempt",
        on_delete=models.CASCADE,
        related_name="items",
    )
    paper_item_id = models.UUIDField()
    assessment_section_id = models.UUIDField(null=True, blank=True)
    question_id = models.UUIDField()
    question_version_id = models.UUIDField()
    presentation_order = models.PositiveIntegerField()
    allocated_marks = models.DecimalField(max_digits=8, decimal_places=4)
    allocated_penalty = models.DecimalField(max_digits=8, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attempts_attempt_item"
        verbose_name = "attempt item"
        verbose_name_plural = "attempt items"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "presentation_order"],
                name="uq_attempt_item_attempt_presentation_order",
            ),
            models.UniqueConstraint(
                fields=["attempt", "paper_item_id"],
                name="uq_attempt_item_attempt_paper_item",
            ),
            models.CheckConstraint(
                condition=models.Q(presentation_order__gte=1),
                name="chk_attempt_item_presentation_order_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(allocated_marks__gte=Decimal("0.0000")),
                name="chk_attempt_item_allocated_marks_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(allocated_penalty__gte=Decimal("0.0000")),
                name="chk_attempt_item_allocated_penalty_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["attempt", "presentation_order"], name="idx_attempt_item_order"),
        ]

    def __str__(self) -> str:
        return f"Item {self.presentation_order} on Attempt {self.attempt_id} (QVersion {self.question_version_id})"

    def clean(self):
        super().clean()
        if self.presentation_order is not None and self.presentation_order < 1:
            raise ValidationError({"presentation_order": "presentation_order must be a positive integer (>= 1)."})
        if self.allocated_marks is not None and self.allocated_marks < Decimal("0.0000"):
            raise ValidationError({"allocated_marks": "allocated_marks cannot be negative."})
        if self.allocated_penalty is not None and self.allocated_penalty < Decimal("0.0000"):
            raise ValidationError({"allocated_penalty": "allocated_penalty cannot be negative."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
