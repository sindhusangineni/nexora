from django.db import models


class QuestionType(models.TextChoices):
    MCQ = "MCQ", "Multiple Choice (Single Answer)"
    MULTIPLE_SELECT = "MULTIPLE_SELECT", "Multiple Select (Multiple Answers)"
    TRUE_FALSE = "TRUE_FALSE", "True / False"
    ASSERTION_REASON = "ASSERTION_REASON", "Assertion and Reason"
    MATCH_FOLLOWING = "MATCH_FOLLOWING", "Match the Following"
    DESCRIPTIVE = "DESCRIPTIVE", "Descriptive / Long Answer"


class Difficulty(models.TextChoices):
    EASY = "EASY", "Easy"
    MEDIUM = "MEDIUM", "Medium"
    HARD = "HARD", "Hard"


class QuestionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    REVIEW = "REVIEW", "Under Review"
    APPROVED = "APPROVED", "Approved"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


class MatchItemSide(models.TextChoices):
    LEFT = "LEFT", "Left Side"
    RIGHT = "RIGHT", "Right Side"


class AssertionReasonRelationship(models.TextChoices):
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


class QuestionSourceType(models.TextChoices):
    ORIGINAL = "ORIGINAL", "Original"
    UPSC_PREVIOUS_YEAR = "UPSC_PREVIOUS_YEAR", "UPSC Previous Year"
    LICENSED = "LICENSED", "Licensed"
    CONTRIBUTOR = "CONTRIBUTOR", "Contributor"
    AI_GENERATED = "AI_GENERATED", "AI Generated"
    IMPORTED = "IMPORTED", "Imported"
