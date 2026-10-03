import uuid
from django.core.exceptions import ValidationError
from django.db import models

from apps.attempts.models.enums import (
    AttemptStatus,
    ScoreFloorPolicy,
    SubmissionReason,
)


class Attempt(models.Model):
    """
    Root aggregate representing one student's historical test execution session.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField(db_index=True)
    assessment_paper_id = models.UUIDField(db_index=True)
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=32,
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS,
    )
    submission_reason = models.CharField(
        max_length=32,
        choices=SubmissionReason.choices,
        null=True,
        blank=True,
    )
    scoring_policy_version = models.CharField(
        max_length=16,
        default="v1",
    )
    score_floor_policy = models.CharField(
        max_length=32,
        choices=ScoreFloorPolicy.choices,
        default=ScoreFloorPolicy.UNRESTRICTED,
    )
    duration_seconds = models.PositiveIntegerField()
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.UUIDField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    presentation_seed = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attempts_attempt"
        verbose_name = "attempt"
        verbose_name_plural = "attempts"
        constraints = [
            models.UniqueConstraint(
                fields=["student_id", "assessment_paper_id", "attempt_number"],
                name="uq_attempt_student_paper_attempt_number",
            ),
            models.CheckConstraint(
                condition=models.Q(attempt_number__gte=1),
                name="chk_attempt_attempt_number_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=1),
                name="chk_attempt_duration_seconds_positive",
            ),
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(status=AttemptStatus.CANCELLED)
                        & models.Q(cancelled_at__isnull=False)
                        & models.Q(cancelled_by__isnull=False)
                        & models.Q(cancellation_reason__isnull=False)
                        & ~models.Q(cancellation_reason="")
                    )
                    | (
                        ~models.Q(status=AttemptStatus.CANCELLED)
                        & models.Q(cancelled_at__isnull=True)
                        & models.Q(cancelled_by__isnull=True)
                        & models.Q(cancellation_reason__isnull=True)
                    )
                ),
                name="chk_attempt_cancellation_metadata",
            ),
        ]
        indexes = [
            models.Index(fields=["student_id", "status"], name="idx_attempt_student_status"),
            models.Index(fields=["assessment_paper_id", "status"], name="idx_attempt_paper_status"),
            models.Index(fields=["expires_at"], name="idx_attempt_expires_at"),
        ]

    def __str__(self) -> str:
        return f"Attempt {self.attempt_number} for Student {self.student_id} on Paper {self.assessment_paper_id} [{self.status}]"

    def clean(self):
        super().clean()
        if self.status == AttemptStatus.CANCELLED:
            if not self.cancelled_at:
                raise ValidationError({"cancelled_at": "cancelled_at is required when status is CANCELLED."})
            if not self.cancelled_by:
                raise ValidationError({"cancelled_by": "cancelled_by is required when status is CANCELLED."})
            if not self.cancellation_reason or not self.cancellation_reason.strip():
                raise ValidationError({"cancellation_reason": "A non-empty cancellation_reason is required when status is CANCELLED."})
        else:
            if self.cancelled_at is not None:
                raise ValidationError({"cancelled_at": "cancelled_at must be NULL when status is not CANCELLED."})
            if self.cancelled_by is not None:
                raise ValidationError({"cancelled_by": "cancelled_by must be NULL when status is not CANCELLED."})
            if self.cancellation_reason is not None:
                raise ValidationError({"cancellation_reason": "cancellation_reason must be NULL when status is not CANCELLED."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
