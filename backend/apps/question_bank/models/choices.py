import uuid
from django.db import models


class QuestionVersionChoice(models.Model):
    """
    Choice content for MCQ and MULTIPLE_SELECT questions.
    Reusable single table for both single-select and multiple-select question types.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_version = models.ForeignKey(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text = models.TextField()
    position = models.PositiveIntegerField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "question_bank_choice"
        verbose_name = "question choice"
        verbose_name_plural = "question choices"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["question_version", "position"],
                name="unique_choice_version_position",
            ),
            models.CheckConstraint(
                condition=models.Q(position__gt=0),
                name="check_positive_choice_position",
            ),
        ]

    def __str__(self) -> str:
        marker = "[X]" if self.is_correct else "[ ]"
        return f"{self.position}. {marker} {self.text[:30]}"

    def clean(self):
        super().clean()
        if hasattr(self, "question_version") and self.question_version:
            from apps.question_bank.exceptions import ContentRepresentationError
            from apps.question_bank.models.enums import QuestionType

            if self.question_version.question_type not in (
                QuestionType.MCQ,
                QuestionType.MULTIPLE_SELECT,
            ):
                raise ContentRepresentationError(
                    f"QuestionVersionChoice can only be associated with MCQ or MULTIPLE_SELECT questions, "
                    f"found '{self.question_version.question_type}'."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
