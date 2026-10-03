import uuid
from django.db import models


class Question(models.Model):
    """
    Conceptual identity of a question.
    Stable across editorial versions.
    Does NOT contain text, question_type, difficulty, status, or explanation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_bank_question"
        verbose_name = "question"
        verbose_name_plural = "questions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Question {self.id}"

    @property
    def published_version(self):
        """Return the currently published version of this question, if any."""
        return self.versions.filter(status="PUBLISHED").first()

    @property
    def latest_version(self):
        """Return the latest version of this question by version number."""
        return self.versions.order_by("-version_number").first()
