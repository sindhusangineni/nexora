import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models

from apps.attempts.models.enums import EvaluationState


class AttemptEvaluation(models.Model):
    """
    Item-level evaluation created during submission/evaluation processing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_item = models.OneToOneField(
        "attempts.AttemptItem",
        on_delete=models.CASCADE,
        related_name="evaluation",
    )
    evaluation_state = models.CharField(
        max_length=32,
        choices=EvaluationState.choices,
    )
    marks_awarded = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    marks_deducted = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    net_marks = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    evaluator_id = models.UUIDField(null=True, blank=True)
    evaluation_comments = models.TextField(null=True, blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "attempts_attempt_evaluation"
        verbose_name = "attempt evaluation"
        verbose_name_plural = "attempt evaluations"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(marks_awarded__gte=Decimal("0.0000")),
                name="chk_attempt_eval_marks_awarded_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(marks_deducted__gte=Decimal("0.0000")),
                name="chk_attempt_eval_marks_deducted_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(evaluation_state__in=[EvaluationState.PENDING_EVALUATION, EvaluationState.UNATTEMPTED])
                        & models.Q(evaluated_at__isnull=True)
                        & models.Q(evaluator_id__isnull=True)
                    )
                    | (
                        models.Q(evaluation_state__in=[EvaluationState.CORRECT, EvaluationState.INCORRECT])
                        & models.Q(evaluated_at__isnull=False)
                    )
                    | (
                        models.Q(evaluation_state=EvaluationState.PARTIALLY_CORRECT)
                        & models.Q(evaluated_at__isnull=False)
                        & models.Q(evaluator_id__isnull=False)
                    )
                ),
                name="chk_attempt_eval_state_evaluated_at",
            ),
        ]

    def __str__(self) -> str:
        return f"Evaluation for Item {self.attempt_item_id} [{self.evaluation_state}]: Net {self.net_marks}"

    def clean(self):
        super().clean()
        if self.marks_awarded is not None and self.marks_awarded < Decimal("0.0000"):
            raise ValidationError({"marks_awarded": "marks_awarded cannot be negative."})
        if self.marks_deducted is not None and self.marks_deducted < Decimal("0.0000"):
            raise ValidationError({"marks_deducted": "marks_deducted cannot be negative."})

        if self.evaluation_state in (EvaluationState.PENDING_EVALUATION, EvaluationState.UNATTEMPTED):
            if self.evaluated_at is not None:
                raise ValidationError({"evaluated_at": f"evaluated_at must be NULL when state is {self.evaluation_state}."})
            if self.evaluator_id is not None:
                raise ValidationError({"evaluator_id": f"evaluator_id must be NULL when state is {self.evaluation_state}."})
        elif self.evaluation_state in (EvaluationState.CORRECT, EvaluationState.INCORRECT):
            if self.evaluated_at is None:
                raise ValidationError({"evaluated_at": f"evaluated_at cannot be NULL when state is {self.evaluation_state}."})
        elif self.evaluation_state == EvaluationState.PARTIALLY_CORRECT:
            if self.evaluated_at is None:
                raise ValidationError({"evaluated_at": "evaluated_at cannot be NULL for PARTIALLY_CORRECT."})
            if self.evaluator_id is None:
                raise ValidationError({"evaluator_id": "evaluator_id is required for PARTIALLY_CORRECT."})

    def save(self, *args, **kwargs):
        if self.marks_awarded is not None and self.marks_deducted is not None:
            self.net_marks = self.marks_awarded - self.marks_deducted
        self.clean()
        super().save(*args, **kwargs)
