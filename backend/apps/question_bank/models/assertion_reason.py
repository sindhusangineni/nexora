from django.core.exceptions import ValidationError
from django.db import models

from apps.question_bank.models.enums import (
    AssertionReasonRelationship,
    QuestionType,
)


class AssertionReasonContent(models.Model):
    """
    Content representation for ASSERTION_REASON questions.
    Stores the assertion, the reason, and the semantic relationship between them.
    Does NOT store UI labels such as A/B/C/D.
    """

    question_version = models.OneToOneField(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="assertion_reason_content",
    )
    assertion = models.TextField()
    reason = models.TextField()
    correct_relationship = models.CharField(
        max_length=64,
        choices=AssertionReasonRelationship.choices,
    )

    class Meta:
        db_table = "question_bank_assertion_reason"
        verbose_name = "assertion reason content"
        verbose_name_plural = "assertion reason contents"

    def __str__(self) -> str:
        return f"AssertionReason for QuestionVersion {self.question_version_id} [{self.correct_relationship}]"

    def clean(self):
        super().clean()
        if (
            hasattr(self, "question_version")
            and self.question_version
            and self.question_version.question_type != QuestionType.ASSERTION_REASON
        ):
            from apps.question_bank.exceptions import ContentRepresentationError

            raise ContentRepresentationError(
                f"AssertionReasonContent can only be associated with question_type '{QuestionType.ASSERTION_REASON}', "
                f"found '{self.question_version.question_type}'."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
