import uuid
from django.db import models

from apps.assessment.exceptions import AssessmentImmutableError, AssessmentValidationError
from apps.assessment.models.enums import (
    AssessmentStatus,
    Difficulty,
    QuestionType,
    ScopeType,
)


class SelectionRule(models.Model):
    """
    Defines criteria for selecting questions into an assessment paper.
    Scope ID is a scalar UUID to preserve strict cross-module isolation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        "assessment.Assessment",
        on_delete=models.CASCADE,
        related_name="selection_rules",
    )
    assessment_section = models.ForeignKey(
        "assessment.AssessmentSection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="selection_rules",
    )
    scope_type = models.CharField(
        max_length=32,
        choices=ScopeType.choices,
    )
    scope_id = models.UUIDField(
        db_index=True,
        help_text="Scalar UUID referencing learning taxonomy entity (Domain/Subject/Chapter/Topic).",
    )
    question_type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
        null=True,
        blank=True,
    )
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
        null=True,
        blank=True,
    )
    question_count = models.PositiveIntegerField(
        help_text="Number of questions to select matching these criteria.",
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="Execution/presentation order of this rule within the assessment.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessment_selection_rule"
        verbose_name = "selection rule"
        verbose_name_plural = "selection rules"
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "position"],
                name="uq_selection_rule_assessment_position",
            ),
        ]

    def __str__(self) -> str:
        sec = f" (Section: {self.assessment_section.title})" if self.assessment_section else ""
        return f"Rule {self.position}: {self.question_count}x {self.scope_type}:{self.scope_id}{sec}"

    def clean(self):
        super().clean()
        if self.question_count is not None and self.question_count < 1:
            raise AssessmentValidationError("Question count must be at least 1.")

        if self.assessment_section_id and self.assessment_id:
            if self.assessment_section.assessment_id != self.assessment_id:
                raise AssessmentValidationError(
                    "Assessment section does not belong to the parent assessment."
                )

    def save(self, *args, **kwargs):
        if self.assessment.status != AssessmentStatus.DRAFT:
            raise AssessmentImmutableError(
                f"Cannot modify selection rules for assessment in '{self.assessment.status}' status."
            )
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.assessment.status != AssessmentStatus.DRAFT:
            raise AssessmentImmutableError(
                f"Cannot delete selection rules for assessment in '{self.assessment.status}' status."
            )
        return super().delete(*args, **kwargs)
