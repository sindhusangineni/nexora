import uuid
from decimal import Decimal
from django.db import models

from apps.assessment.exceptions import AssessmentPaperImmutableError


class AssessmentPaperItem(models.Model):
    """
    Immutable question snapshot pinned to an exact QuestionVersion within an AssessmentPaper.
    Maintains deterministic presentation order and allocated marking rules.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paper = models.ForeignKey(
        "assessment.AssessmentPaper",
        on_delete=models.CASCADE,
        related_name="items",
    )
    question_id = models.UUIDField(
        db_index=True,
        help_text="Stable conceptual Question ID (scalar UUID).",
    )
    question_version_id = models.UUIDField(
        db_index=True,
        help_text="Exact pinned published QuestionVersion ID (scalar UUID).",
    )
    assessment_section = models.ForeignKey(
        "assessment.AssessmentSection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paper_items",
    )
    presentation_order = models.PositiveIntegerField(
        help_text="1-based presentation sequence of this item in the paper.",
    )
    allocated_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Marks allocated for answering this item correctly.",
    )
    allocated_penalty = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Penalty deducted for answering this item incorrectly.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_paper_item"
        verbose_name = "assessment paper item"
        verbose_name_plural = "assessment paper items"
        ordering = ["presentation_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["paper", "presentation_order"],
                name="uq_paper_item_presentation_order",
            ),
            models.UniqueConstraint(
                fields=["paper", "question_id"],
                name="uq_paper_item_question_id",
            ),
        ]

    def __str__(self) -> str:
        return f"Item {self.presentation_order} on Paper {self.paper_id} (Q: {self.question_id})"

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            if AssessmentPaperItem.objects.filter(pk=self.pk).exists():
                raise AssessmentPaperImmutableError(
                    "AssessmentPaperItem is immutable once created."
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssessmentPaperImmutableError(
            "AssessmentPaperItem is immutable and cannot be deleted individually."
        )
