from apps.learning.filters import DomainFilter
from apps.learning.selectors import get_domains_queryset
from apps.learning.serializers import DomainSerializer
from apps.learning.views.base import LearningBaseViewSet


class DomainViewSet(LearningBaseViewSet):
    serializer_class = DomainSerializer
    filterset_class = DomainFilter

    def get_queryset(self):
        return get_domains_queryset()
