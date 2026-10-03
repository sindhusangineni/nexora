from django.db import models


class AssessmentType(models.TextChoices):
    PRACTICE = "PRACTICE", "Practice"
    REVISION = "REVISION", "Revision"
    MOCK = "MOCK", "Mock"
    CUSTOM = "CUSTOM", "Custom"


class AssessmentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


class ScopeType(models.TextChoices):
    DOMAIN = "DOMAIN", "Domain"
    SUBJECT = "SUBJECT", "Subject"
    CHAPTER = "CHAPTER", "Chapter"
    TOPIC = "TOPIC", "Topic"


class PaperStatus(models.TextChoices):
    GENERATED = "GENERATED", "Generated"


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
