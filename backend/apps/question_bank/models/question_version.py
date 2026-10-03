import uuid
from django.db import models
from django.db.models.deletion import ProtectedError

from apps.question_bank.models.enums import (
    Difficulty,
    QuestionSourceType,
    QuestionStatus,
    QuestionType,
)
from apps.question_bank.validators import (
    validate_single_content_representation,
    validate_status_transition,
    validate_version_for_publication,
    validate_version_immutability,
)


class QuestionVersion(models.Model):
    """
    Represents an editorial version of a conceptual Question.
    Approved, published, and archived versions are immutable.
    Draft versions may be edited.
    Version numbers are strictly positive and never reused.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        "question_bank.Question",
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    question_type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
    )
    text = models.TextField()
    explanation = models.TextField(blank=True, default="")
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
    )
    status = models.CharField(
        max_length=16,
        choices=QuestionStatus.choices,
        default=QuestionStatus.DRAFT,
    )
    # Provenance metadata (Phase 1.1)
    source_type = models.CharField(
        max_length=32,
        choices=QuestionSourceType.choices,
        null=True,
        blank=True,
    )
    source_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    source_reference = models.CharField(
        max_length=512,
        null=True,
        blank=True,
    )
    source_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    external_question_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_bank_question_version"
        verbose_name = "question version"
        verbose_name_plural = "question versions"
        ordering = ["question", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "version_number"],
                name="unique_question_version_number",
            ),
            models.CheckConstraint(
                condition=models.Q(version_number__gt=0),
                name="check_positive_version_number",
            ),
            models.UniqueConstraint(
                fields=["question"],
                condition=models.Q(status=QuestionStatus.PUBLISHED),
                name="unique_published_version_per_question",
            ),
        ]

    def __str__(self) -> str:
        return f"Question {self.question_id} v{self.version_number} [{self.status}]"

    def clean(self):
        super().clean()
        if self.pk:
            orig = QuestionVersion.objects.filter(pk=self.pk).first()
            if orig:
                validate_version_immutability(orig, self)
                if orig.status != self.status:
                    validate_status_transition(orig.status, self.status)
                    if self.status == QuestionStatus.PUBLISHED:
                        validate_single_content_representation(self)
                        validate_version_for_publication(self)
                if orig.question_type != self.question_type:
                    has_any_content = (
                        self.choices.exists()
                        or hasattr(self, "true_false_content")
                        or hasattr(self, "assertion_reason_content")
                        or hasattr(self, "match_following_content")
                        or hasattr(self, "descriptive_content")
                    )
                    if has_any_content:
                        from apps.question_bank.exceptions import ContentRepresentationError

                        raise ContentRepresentationError(
                            f"Cannot change question_type from '{orig.question_type}' to '{self.question_type}' "
                            f"while existing content representations exist. Remove existing content first."
                        )
            else:
                if self.status != QuestionStatus.DRAFT:
                    from apps.question_bank.exceptions import InvalidStatusTransitionError

                    raise InvalidStatusTransitionError(
                        f"New question versions must be created in DRAFT status. Cannot create with status '{self.status}'."
                    )
        else:
            if self.status != QuestionStatus.DRAFT:
                from apps.question_bank.exceptions import InvalidStatusTransitionError

                raise InvalidStatusTransitionError(
                    f"New question versions must be created in DRAFT status. Cannot create with status '{self.status}'."
                )

    def save(self, *args, **kwargs):
        if self.pk:
            orig = QuestionVersion.objects.filter(pk=self.pk).first()
            if orig:
                validate_version_immutability(orig, self)
                if orig.status != self.status:
                    validate_status_transition(orig.status, self.status)
                    if self.status == QuestionStatus.PUBLISHED:
                        validate_single_content_representation(self)
                        validate_version_for_publication(self)
                if orig.question_type != self.question_type:
                    has_any_content = (
                        self.choices.exists()
                        or hasattr(self, "true_false_content")
                        or hasattr(self, "assertion_reason_content")
                        or hasattr(self, "match_following_content")
                        or hasattr(self, "descriptive_content")
                    )
                    if has_any_content:
                        from apps.question_bank.exceptions import ContentRepresentationError

                        raise ContentRepresentationError(
                            f"Cannot change question_type from '{orig.question_type}' to '{self.question_type}' "
                            f"while existing content representations exist. Remove existing content first."
                        )
            else:
                if self.status != QuestionStatus.DRAFT:
                    from apps.question_bank.exceptions import InvalidStatusTransitionError

                    raise InvalidStatusTransitionError(
                        f"New question versions must be created in DRAFT status. Cannot create with status '{self.status}'."
                    )
        else:
            if self.status != QuestionStatus.DRAFT:
                from apps.question_bank.exceptions import InvalidStatusTransitionError

                raise InvalidStatusTransitionError(
                    f"New question versions must be created in DRAFT status. Cannot create with status '{self.status}'."
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status in (
            QuestionStatus.APPROVED,
            QuestionStatus.PUBLISHED,
            QuestionStatus.ARCHIVED,
        ):
            raise ProtectedError(
                f"Cannot delete question version with status '{self.status}'. "
                f"Approved, published, and archived versions are permanent historical records.",
                [self],
            )
        return super().delete(*args, **kwargs)
