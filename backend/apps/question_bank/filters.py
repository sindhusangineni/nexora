import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from apps.question_bank.models import (
    Difficulty,
    Question,
    QuestionStatus,
    QuestionType,
    QuestionVersion,
)


class QuestionBankFilterBackend(DjangoFilterBackend):
    """
    Custom DjangoFilterBackend that raises a ValidationError on invalid filter inputs
    (such as malformed UUIDs), ensuring standard Nexora 400 VALIDATION_ERROR envelopes.
    """

    raise_exception = True


class QuestionFilter(FilterSet):
    """
    FilterSet for the Question aggregate root collection.
    Supports filtering by topic, question_type, difficulty, status, and case-insensitive search.
    """

    topic = django_filters.UUIDFilter(
        field_name="question_topics__topic_id",
        help_text="Filter questions associated with a specific Learning Topic UUID.",
    )
    question_type = django_filters.ChoiceFilter(
        field_name="versions__question_type",
        choices=QuestionType.choices,
        help_text="Filter questions that have a version matching the question_type.",
    )
    difficulty = django_filters.ChoiceFilter(
        field_name="versions__difficulty",
        choices=Difficulty.choices,
        help_text="Filter questions that have a version matching the difficulty.",
    )
    status = django_filters.ChoiceFilter(
        field_name="versions__status",
        choices=QuestionStatus.choices,
        help_text="Filter questions that have a version matching the lifecycle status.",
    )
    search = django_filters.CharFilter(
        method="filter_search",
        help_text="Case-insensitive search across question version text and explanation.",
    )

    class Meta:
        model = Question
        fields = ["topic", "question_type", "difficulty", "status", "search"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(versions__text__icontains=value)
            | Q(versions__explanation__icontains=value)
        ).distinct()

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).distinct()


class QuestionVersionFilter(FilterSet):
    """
    FilterSet for QuestionVersion collections belonging to a specific Question.
    """

    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=QuestionStatus.choices,
        help_text="Filter versions by lifecycle status.",
    )
    question_type = django_filters.ChoiceFilter(
        field_name="question_type",
        choices=QuestionType.choices,
        help_text="Filter versions by question type.",
    )
    difficulty = django_filters.ChoiceFilter(
        field_name="difficulty",
        choices=Difficulty.choices,
        help_text="Filter versions by difficulty.",
    )
    search = django_filters.CharFilter(
        method="filter_search",
        help_text="Case-insensitive search across version text and explanation.",
    )

    class Meta:
        model = QuestionVersion
        fields = ["status", "question_type", "difficulty", "search"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(text__icontains=value) | Q(explanation__icontains=value)
        )
