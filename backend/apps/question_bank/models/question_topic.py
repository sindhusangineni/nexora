import uuid
from django.db import models


class QuestionTopic(models.Model):
    """
    Associates a conceptual Question with a Learning Topic.
    Topics describe the stable conceptual Question, not an individual editorial version.
    Question Bank owns this relationship. Learning must NOT import Question Bank.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        "question_bank.Question",
        on_delete=models.CASCADE,
        related_name="question_topics",
    )
    topic = models.ForeignKey(
        "learning.Topic",
        on_delete=models.PROTECT,
        related_name="question_topics",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_bank_question_topic"
        verbose_name = "question topic"
        verbose_name_plural = "question topics"
        indexes = [
            models.Index(
                fields=["topic", "question"],
                name="idx_qtopic_topic_question",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "topic"],
                name="unique_question_topic",
            ),
        ]

    def __str__(self) -> str:
        return f"Question {self.question_id} <-> Topic {self.topic_id}"
