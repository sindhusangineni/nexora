from apps.learning.filters import SubjectFilter
from apps.learning.selectors import get_subjects_queryset
from apps.learning.serializers import SubjectSerializer
from apps.learning.views.base import LearningBaseViewSet


class SubjectViewSet(LearningBaseViewSet):
    serializer_class = SubjectSerializer
    filterset_class = SubjectFilter

    def get_queryset(self):
        return get_subjects_queryset()
