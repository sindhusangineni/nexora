from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.response import Response

from shared.api.errors import ErrorResponseSerializer
from apps.learning.filters import LearningFilterBackend
from apps.learning.pagination import LearningPagination
from apps.learning.permissions import IsSuperadminOrReadOnlyAuthenticated
from apps.learning.services import delete_curriculum_resource


@extend_schema(
    tags=["Learning"],
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        status.HTTP_409_CONFLICT: ErrorResponseSerializer,
    },
)
class LearningBaseViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Base ViewSet for Learning curriculum resources:
    - Exposes GET, POST, PATCH, DELETE, HEAD, OPTIONS strictly.
    - PUT is deliberately not exposed or routed.
    - Applies standard Learning authentication & RBAC policy.
    - Applies custom pagination with page_size support.
    - Applies strict filter backend raising 400 on malformed query inputs.
    - Enforces protected deletion via the curriculum deletion service (409 Conflict).
    - Handles concurrent uniqueness races gracefully.
    """

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [IsSuperadminOrReadOnlyAuthenticated]
    pagination_class = LearningPagination
    filter_backends = (LearningFilterBackend,)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        delete_curriculum_resource(instance)

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise serializers.ValidationError(
                {"name": ["An entity with this name already exists in this scope."]}
            )

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise serializers.ValidationError(
                {"name": ["An entity with this name already exists in this scope."]}
            )
