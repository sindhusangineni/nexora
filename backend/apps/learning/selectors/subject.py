from django.db.models import QuerySet

from apps.learning.models import Subject


def get_subjects_queryset() -> QuerySet[Subject]:
    """Return base queryset for Subject with eager-loaded parent domain and deterministic ordering."""
    return Subject.objects.select_related("domain").order_by("position", "name")
