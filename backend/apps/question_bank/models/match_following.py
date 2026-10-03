import uuid
from django.core.exceptions import ValidationError
from django.db import models

from apps.question_bank.models.enums import MatchItemSide, QuestionType


class MatchFollowingContent(models.Model):
    """
    Parent anchor for MATCH_FOLLOWING question content.
    """

    question_version = models.OneToOneField(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="match_following_content",
    )

    class Meta:
        db_table = "question_bank_match_following"
        verbose_name = "match following content"
        verbose_name_plural = "match following contents"

    def __str__(self) -> str:
        return f"MatchFollowing for QuestionVersion {self.question_version_id}"

    def clean(self):
        super().clean()
        if (
            hasattr(self, "question_version")
            and self.question_version
            and self.question_version.question_type != QuestionType.MATCH_FOLLOWING
        ):
            from apps.question_bank.exceptions import ContentRepresentationError

            raise ContentRepresentationError(
                f"MatchFollowingContent can only be associated with question_type '{QuestionType.MATCH_FOLLOWING}', "
                f"found '{self.question_version.question_type}'."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class MatchFollowingItem(models.Model):
    """
    Individual items to be matched on the LEFT or RIGHT side.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_version = models.ForeignKey(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        related_name="match_items",
    )
    side = models.CharField(
        max_length=8,
        choices=MatchItemSide.choices,
    )
    text = models.TextField()
    position = models.PositiveIntegerField()

    class Meta:
        db_table = "question_bank_match_item"
        verbose_name = "match following item"
        verbose_name_plural = "match following items"
        ordering = ["side", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["question_version", "side", "position"],
                name="unique_match_item_side_pos",
            ),
            models.CheckConstraint(
                condition=models.Q(position__gt=0),
                name="check_positive_match_item_pos",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.side}] {self.position}. {self.text[:30]}"

    def clean(self):
        super().clean()
        if hasattr(self, "question_version") and self.question_version:
            from apps.question_bank.exceptions import ContentRepresentationError

            if self.question_version.question_type != QuestionType.MATCH_FOLLOWING:
                raise ContentRepresentationError(
                    f"MatchFollowingItem can only be associated with question_type '{QuestionType.MATCH_FOLLOWING}', "
                    f"found '{self.question_version.question_type}'."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class MatchFollowingPair(models.Model):
    """
    Defines the correct 1-to-1 matching key between a LEFT item and a RIGHT item.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_version = models.ForeignKey(
        "question_bank.QuestionVersion",
        on_delete=models.CASCADE,
        related_name="match_pairs",
    )
    left_item = models.ForeignKey(
        "question_bank.MatchFollowingItem",
        on_delete=models.CASCADE,
        related_name="left_pairs",
    )
    right_item = models.ForeignKey(
        "question_bank.MatchFollowingItem",
        on_delete=models.CASCADE,
        related_name="right_pairs",
    )

    class Meta:
        db_table = "question_bank_match_pair"
        verbose_name = "match following pair"
        verbose_name_plural = "match following pairs"
        constraints = [
            models.UniqueConstraint(
                fields=["question_version", "left_item"],
                name="unique_match_pair_left",
            ),
            models.UniqueConstraint(
                fields=["question_version", "right_item"],
                name="unique_match_pair_right",
            ),
        ]

    def __str__(self) -> str:
        return f"Pair ({self.left_item_id} <-> {self.right_item_id})"

    def clean(self):
        super().clean()
        from apps.question_bank.exceptions import ContentRepresentationError

        if hasattr(self, "question_version") and self.question_version:
            if self.question_version.question_type != QuestionType.MATCH_FOLLOWING:
                raise ContentRepresentationError(
                    f"MatchFollowingPair can only be associated with question_type '{QuestionType.MATCH_FOLLOWING}', "
                    f"found '{self.question_version.question_type}'."
                )

        if hasattr(self, "left_item") and self.left_item:
            if self.left_item.side != MatchItemSide.LEFT:
                raise ValidationError("left_item must belong to the LEFT side.")
            if self.left_item.question_version_id != self.question_version_id:
                raise ValidationError("left_item must belong to the same QuestionVersion as the pair.")

        if hasattr(self, "right_item") and self.right_item:
            if self.right_item.side != MatchItemSide.RIGHT:
                raise ValidationError("right_item must belong to the RIGHT side.")
            if self.right_item.question_version_id != self.question_version_id:
                raise ValidationError("right_item must belong to the same QuestionVersion as the pair.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
