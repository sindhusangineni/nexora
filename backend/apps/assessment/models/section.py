import uuid
from django.db import models

from apps.assessment.exceptions import AssessmentImmutableError
from apps.assessment.models.enums import AssessmentStatus


class AssessmentSection(models.Model):
    """
    Optional section within an Assessment to organize items and rules.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        "assessment.Assessment",
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessment_section"
        verbose_name = "assessment section"
        verbose_name_plural = "assessment sections"
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "position"],
                name="uq_assessment_section_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assessment.title} - Section {self.position}: {self.title}"

    def save(self, *args, **kwargs):
        if self.assessment.status != AssessmentStatus.DRAFT:
            raise AssessmentImmutableError(
                f"Cannot modify sections for assessment in '{self.assessment.status}' status."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.assessment.status != AssessmentStatus.DRAFT:
            raise AssessmentImmutableError(
                f"Cannot delete sections for assessment in '{self.assessment.status}' status."
            )
        return super().delete(*args, **kwargs)
