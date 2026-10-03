from django.db.models import QuerySet

from apps.learning.models import Chapter


def get_chapters_queryset() -> QuerySet[Chapter]:
    """Return base queryset for Chapter with eager-loaded parent subject and deterministic ordering."""
    return Chapter.objects.select_related("subject").order_by("position", "name")
