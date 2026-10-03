from django.db.models import Q
import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from apps.learning.models import Chapter, Domain, Subject, Topic


class LearningFilterBackend(DjangoFilterBackend):
    """
    Custom DjangoFilterBackend that raises a ValidationError on invalid filter inputs
    (such as malformed UUIDs), ensuring standard Nexora 400 VALIDATION_ERROR envelopes.
    """

    raise_exception = True


class BaseCurriculumFilter(FilterSet):
    """
    Base filter set for curriculum entities supporting unified case-insensitive search
    across name and description.
    """

    search = django_filters.CharFilter(
        method="filter_search",
        help_text="Case-insensitive search across name and description.",
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class DomainFilter(BaseCurriculumFilter):
    class Meta:
        model = Domain
        fields = ["search"]


class SubjectFilter(BaseCurriculumFilter):
    domain = django_filters.UUIDFilter(field_name="domain_id")

    class Meta:
        model = Subject
        fields = ["domain", "search"]


class ChapterFilter(BaseCurriculumFilter):
    subject = django_filters.UUIDFilter(field_name="subject_id")

    class Meta:
        model = Chapter
        fields = ["subject", "search"]


class TopicFilter(BaseCurriculumFilter):
    chapter = django_filters.UUIDFilter(field_name="chapter_id")

    class Meta:
        model = Topic
        fields = ["chapter", "search"]
