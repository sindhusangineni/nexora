from apps.learning.filters import ChapterFilter
from apps.learning.selectors import get_chapters_queryset
from apps.learning.serializers import ChapterSerializer
from apps.learning.views.base import LearningBaseViewSet


class ChapterViewSet(LearningBaseViewSet):
    serializer_class = ChapterSerializer
    filterset_class = ChapterFilter

    def get_queryset(self):
        return get_chapters_queryset()
