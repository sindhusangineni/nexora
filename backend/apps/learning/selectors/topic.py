from django.db.models import QuerySet

from apps.learning.models import Topic


def get_topics_queryset() -> QuerySet[Topic]:
    """Return base queryset for Topic with eager-loaded parent chapter and deterministic ordering."""
    return Topic.objects.select_related("chapter").order_by("position", "name")
