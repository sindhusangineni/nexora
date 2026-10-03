from django.core.exceptions import ValidationError
from django.db import models

from apps.question_bank.models.enums import QuestionType


class TrueFalseContent(models.Model):
    """
    Content representation for TRUE_FALSE questions.
    There may be at most one content row per QuestionVersion.
    """

    question_version = models.OneToOneField(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="true_false_content",
    )
    answer = models.BooleanField()

    class Meta:
        db_table = "question_bank_true_false"
        verbose_name = "true false content"
        verbose_name_plural = "true false contents"

    def __str__(self) -> str:
        return f"QuestionVersion {self.question_version_id} Answer: {self.answer}"

    def clean(self):
        super().clean()
        if (
            hasattr(self, "question_version")
            and self.question_version
            and self.question_version.question_type != QuestionType.TRUE_FALSE
        ):
            from apps.question_bank.exceptions import ContentRepresentationError

            raise ContentRepresentationError(
                f"TrueFalseContent can only be associated with question_type '{QuestionType.TRUE_FALSE}', "
                f"found '{self.question_version.question_type}'."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
