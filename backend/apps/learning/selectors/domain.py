from django.db.models import QuerySet

from apps.learning.models import Domain


def get_domains_queryset() -> QuerySet[Domain]:
    """Return base queryset for Domain with deterministic ordering."""
    return Domain.objects.all().order_by("name")
