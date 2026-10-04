from apps.learning.filters import TopicFilter
from apps.learning.selectors import get_topics_queryset
from apps.learning.serializers import TopicSerializer
from apps.learning.views.base import LearningBaseViewSet


class TopicViewSet(LearningBaseViewSet):
    serializer_class = TopicSerializer
    filterset_class = TopicFilter

    def get_queryset(self):
        return get_topics_queryset()
