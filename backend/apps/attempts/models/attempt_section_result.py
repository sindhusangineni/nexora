import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models


class AttemptSectionResult(models.Model):
    """
    Historical sectional result snapshot.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_result = models.ForeignKey(
        "attempts.AttemptResult",
        on_delete=models.CASCADE,
        related_name="section_results",
    )
    assessment_section_id = models.UUIDField()
    section_title_snapshot = models.CharField(max_length=255)
    section_order_snapshot = models.PositiveIntegerField()
    score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    maximum_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    attempted_questions = models.PositiveIntegerField(default=0)
    correct_questions = models.PositiveIntegerField(default=0)
    incorrect_questions = models.PositiveIntegerField(default=0)
    partially_correct_questions = models.PositiveIntegerField(default=0)
    unanswered_questions = models.PositiveIntegerField(default=0)
    pending_evaluation_questions = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "attempts_attempt_section_result"
        verbose_name = "attempt section result"
        verbose_name_plural = "attempt section results"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt_result", "assessment_section_id"],
                name="uq_attempt_section_result_result_section",
            ),
            models.CheckConstraint(
                condition=models.Q(section_order_snapshot__gte=1),
                name="chk_attempt_sec_res_section_order_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    attempted_questions=models.F("correct_questions")
                    + models.F("incorrect_questions")
                    + models.F("partially_correct_questions")
                ),
                name="chk_attempt_sec_res_attempted_checksum",
            ),
        ]
        indexes = [
            models.Index(fields=["attempt_result", "assessment_section_id"], name="idx_attempt_sec_res_sec"),
        ]

    def __str__(self) -> str:
        return f"Section '{self.section_title_snapshot}' on Result {self.attempt_result_id}: {self.score}/{self.maximum_score}"

    def clean(self):
        super().clean()
        if self.section_order_snapshot is not None and self.section_order_snapshot < 1:
            raise ValidationError({"section_order_snapshot": "section_order_snapshot must be a positive integer (>= 1)."})

        expected_attempted = (
            (self.correct_questions or 0)
            + (self.incorrect_questions or 0)
            + (self.partially_correct_questions or 0)
        )
        if self.attempted_questions != expected_attempted:
            raise ValidationError({
                "attempted_questions": (
                    f"attempted_questions ({self.attempted_questions}) must equal "
                    f"correct ({self.correct_questions}) + incorrect ({self.incorrect_questions}) + "
                    f"partially_correct ({self.partially_correct_questions}) = {expected_attempted}."
                )
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
