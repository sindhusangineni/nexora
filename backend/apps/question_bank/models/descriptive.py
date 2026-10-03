from django.core.exceptions import ValidationError
from django.db import models

from apps.question_bank.models.enums import QuestionType


class DescriptiveContent(models.Model):
    """
    Content representation for DESCRIPTIVE questions.
    Stores the maximum marks and the reference/expected answer rubric.
    Does NOT store student responses (which belong to Attempts).
    """

    question_version = models.OneToOneField(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="descriptive_content",
    )
    marks = models.PositiveIntegerField()
    expected_answer = models.TextField()

    class Meta:
        db_table = "question_bank_descriptive"
        verbose_name = "descriptive content"
        verbose_name_plural = "descriptive contents"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(marks__gt=0),
                name="check_positive_descriptive_marks",
            ),
        ]

    def __str__(self) -> str:
        return f"DescriptiveContent for QuestionVersion {self.question_version_id} ({self.marks} marks)"

    def clean(self):
        super().clean()
        if (
            hasattr(self, "question_version")
            and self.question_version
            and self.question_version.question_type != QuestionType.DESCRIPTIVE
        ):
            from apps.question_bank.exceptions import ContentRepresentationError

            raise ContentRepresentationError(
                f"DescriptiveContent can only be associated with question_type '{QuestionType.DESCRIPTIVE}', "
                f"found '{self.question_version.question_type}'."
            )
        if self.marks is not None and self.marks <= 0:
            raise ValidationError("Marks must be a strictly positive integer.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
