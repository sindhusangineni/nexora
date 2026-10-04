import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models

from apps.attempts.models.enums import AttemptResultStatus


class AttemptResult(models.Model):
    """
    Historical aggregate scorecard created when an Attempt reaches SUBMITTED.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.OneToOneField(
        "attempts.Attempt",
        on_delete=models.CASCADE,
        related_name="result",
    )
    status = models.CharField(
        max_length=16,
        choices=AttemptResultStatus.choices,
        default=AttemptResultStatus.PENDING,
    )
    raw_score = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
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
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_questions = models.PositiveIntegerField(default=0)
    attempted_questions = models.PositiveIntegerField(default=0)
    correct_questions = models.PositiveIntegerField(default=0)
    incorrect_questions = models.PositiveIntegerField(default=0)
    partially_correct_questions = models.PositiveIntegerField(default=0)
    unanswered_questions = models.PositiveIntegerField(default=0)
    pending_evaluation_questions = models.PositiveIntegerField(default=0)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attempts_attempt_result"
        verbose_name = "attempt result"
        verbose_name_plural = "attempt results"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    attempted_questions=models.F("correct_questions")
                    + models.F("incorrect_questions")
                    + models.F("partially_correct_questions")
                ),
                name="chk_attempt_result_attempted_checksum",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    total_questions=models.F("attempted_questions")
                    + models.F("unanswered_questions")
                    + models.F("pending_evaluation_questions")
                ),
                name="chk_attempt_result_total_checksum",
            ),
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(status=AttemptResultStatus.FINAL)
                        & models.Q(pending_evaluation_questions=0)
                        & models.Q(finalized_at__isnull=False)
                    )
                    | (
                        ~models.Q(status=AttemptResultStatus.FINAL)
                        & models.Q(finalized_at__isnull=True)
                    )
                ),
                name="chk_attempt_result_final_invariants",
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="idx_attempt_result_status"),
        ]

    def __str__(self) -> str:
        return f"Result for Attempt {self.attempt_id} [{self.status}]: {self.score}/{self.maximum_score} ({self.percentage}%)"

    def clean(self):
        super().clean()
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

        expected_total = (
            (self.attempted_questions or 0)
            + (self.unanswered_questions or 0)
            + (self.pending_evaluation_questions or 0)
        )
        if self.total_questions != expected_total:
            raise ValidationError({
                "total_questions": (
                    f"total_questions ({self.total_questions}) must equal "
                    f"attempted ({self.attempted_questions}) + unanswered ({self.unanswered_questions}) + "
                    f"pending_evaluation ({self.pending_evaluation_questions}) = {expected_total}."
                )
            })

        if self.status == AttemptResultStatus.FINAL:
            if self.pending_evaluation_questions != 0:
                raise ValidationError({
                    "pending_evaluation_questions": "pending_evaluation_questions must be 0 when status is FINAL."
                })
            if self.finalized_at is None:
                raise ValidationError({
                    "finalized_at": "finalized_at cannot be NULL when status is FINAL."
                })
        else:
            if self.finalized_at is not None:
                raise ValidationError({
                    "finalized_at": "finalized_at must be NULL when status is not FINAL."
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
