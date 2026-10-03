from django.db import models


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    SUBMITTED = "SUBMITTED", "Submitted"
    EVALUATED = "EVALUATED", "Evaluated"
    CANCELLED = "CANCELLED", "Cancelled"


class SubmissionReason(models.TextChoices):
    MANUAL = "MANUAL", "Manual"
    TIMEOUT = "TIMEOUT", "Timeout"
    ADMIN_FORCED = "ADMIN_FORCED", "Admin Forced"


class ScoreFloorPolicy(models.TextChoices):
    UNRESTRICTED = "UNRESTRICTED", "Unrestricted"
    ZERO_FLOOR_TOTAL = "ZERO_FLOOR_TOTAL", "Zero Floor Total"
    ZERO_FLOOR_SECTION = "ZERO_FLOOR_SECTION", "Zero Floor Section"


class AnswerState(models.TextChoices):
    UNANSWERED = "UNANSWERED", "Unanswered"
    ANSWERED = "ANSWERED", "Answered"


class AssertionReasonResponse(models.TextChoices):
    BOTH_TRUE_REASON_CORRECT = (
        "BOTH_TRUE_REASON_CORRECT",
        "Both Assertion and Reason are true, and Reason is the correct explanation of Assertion",
    )
    BOTH_TRUE_REASON_NOT_CORRECT = (
        "BOTH_TRUE_REASON_NOT_CORRECT",
        "Both Assertion and Reason are true, but Reason is NOT the correct explanation of Assertion",
    )
    ASSERTION_TRUE_REASON_FALSE = (
        "ASSERTION_TRUE_REASON_FALSE",
        "Assertion is true, but Reason is false",
    )
    ASSERTION_FALSE_REASON_FALSE = (
        "ASSERTION_FALSE_REASON_FALSE",
        "Assertion is false, and Reason is false",
    )


class EvaluationState(models.TextChoices):
    UNATTEMPTED = "UNATTEMPTED", "Unattempted"
    CORRECT = "CORRECT", "Correct"
    INCORRECT = "INCORRECT", "Incorrect"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT", "Partially Correct"
    PENDING_EVALUATION = "PENDING_EVALUATION", "Pending Evaluation"


class AttemptResultStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    FINAL = "FINAL", "Final"
    VOID = "VOID", "Void"
