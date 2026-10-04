import uuid
from decimal import Decimal
from django.db import models

from apps.assessment.exceptions import (
    AssessmentImmutableError,
    AssessmentValidationError,
    InvalidStatusTransitionError,
)
from apps.assessment.models.enums import AssessmentStatus, AssessmentType


class Assessment(models.Model):
    """
    Root aggregate defining an assessment specification and its lifecycle.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    type = models.CharField(
        max_length=32,
        choices=AssessmentType.choices,
        default=AssessmentType.PRACTICE,
    )
    status = models.CharField(
        max_length=32,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.DRAFT,
        db_index=True,
    )
    duration_seconds = models.PositiveIntegerField(
        default=3600,
        help_text="Configured assessment duration in seconds.",
    )
    marks_per_question = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("2.00"),
        help_text="Marks awarded per correct question.",
    )
    penalty_per_question = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.66"),
        help_text="Marks deducted per incorrect question.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessment_assessment"
        verbose_name = "assessment"
        verbose_name_plural = "assessments"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    def can_edit(self) -> bool:
        return self.status == AssessmentStatus.DRAFT

    def publish(self) -> None:
        """
        Transitions an Assessment from DRAFT to PUBLISHED.
        Validates that selection rules and timing/marking configuration exist.
        """
        if self.status != AssessmentStatus.DRAFT:
            raise InvalidStatusTransitionError(
                f"Cannot publish assessment in '{self.status}' status. "
                "Only DRAFT assessments can be published."
            )

        if self.duration_seconds <= 0:
            raise AssessmentValidationError("Assessment duration must be greater than 0 seconds.")

        if self.marks_per_question <= Decimal("0.00"):
            raise AssessmentValidationError("Marks per question must be greater than 0.")

        if self.penalty_per_question < Decimal("0.00"):
            raise AssessmentValidationError("Penalty per question cannot be negative.")

        if not self.selection_rules.exists():
            raise AssessmentValidationError("Cannot publish assessment without at least one selection rule.")

        total_questions = sum(self.selection_rules.values_list("question_count", flat=True))
        if total_questions <= 0:
            raise AssessmentValidationError("Total question count across selection rules must be greater than 0.")

        self.status = AssessmentStatus.PUBLISHED
        self.save(update_fields=["status", "updated_at"])

    def archive(self) -> None:
        """
        Transitions an Assessment from PUBLISHED to ARCHIVED.
        ARCHIVED assessments are permanently read-only.
        """
        if self.status != AssessmentStatus.PUBLISHED:
            raise InvalidStatusTransitionError(
                f"Cannot archive assessment in '{self.status}' status. "
                "Only PUBLISHED assessments can be archived."
            )

        self.status = AssessmentStatus.ARCHIVED
        self.save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            original = Assessment.objects.filter(pk=self.pk).values("status").first()
            if original:
                orig_status = original["status"]
                # If already ARCHIVED, no modifications allowed
                if orig_status == AssessmentStatus.ARCHIVED:
                    raise AssessmentImmutableError("ARCHIVED assessments are permanently immutable.")
                # If PUBLISHED, only status transition to ARCHIVED is permitted
                if orig_status == AssessmentStatus.PUBLISHED and self.status == AssessmentStatus.PUBLISHED:
                    update_fields = kwargs.get("update_fields")
                    if update_fields is None or any(f not in {"status", "updated_at"} for f in update_fields):
                        raise AssessmentImmutableError("PUBLISHED assessments cannot be modified. Archive instead.")
                elif orig_status == AssessmentStatus.PUBLISHED and self.status == AssessmentStatus.DRAFT:
                    raise InvalidStatusTransitionError("Cannot move assessment from PUBLISHED back to DRAFT.")

        super().save(*args, **kwargs)
