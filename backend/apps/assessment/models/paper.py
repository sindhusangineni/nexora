import uuid
from decimal import Decimal
from django.db import models

from apps.assessment.exceptions import AssessmentPaperImmutableError
from apps.assessment.models.enums import PaperStatus


class AssessmentPaper(models.Model):
    """
    Frozen historical test delivery snapshot generated from an Assessment definition.
    Once generated, paper metadata, duration, marking, and items are completely immutable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        "assessment.Assessment",
        on_delete=models.PROTECT,
        related_name="papers",
    )
    status = models.CharField(
        max_length=32,
        choices=PaperStatus.choices,
        default=PaperStatus.GENERATED,
    )
    duration_seconds = models.PositiveIntegerField(
        help_text="Snapshot of duration in seconds at paper generation time.",
    )
    marks_per_question = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Snapshot of marks per question at paper generation time.",
    )
    penalty_per_question = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Snapshot of penalty per question at paper generation time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_paper"
        verbose_name = "assessment paper"
        verbose_name_plural = "assessment papers"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Paper {self.id} (Assessment: {self.assessment.title})"

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            # Check if this row already exists in the database
            if AssessmentPaper.objects.filter(pk=self.pk).exists():
                raise AssessmentPaperImmutableError(
                    "AssessmentPaper is a frozen historical artifact and cannot be modified."
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssessmentPaperImmutableError(
            "AssessmentPaper is a frozen historical artifact and cannot be deleted."
        )
