from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


class DocsDisabledMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "ENABLE_API_DOCS", False):
            raise Http404("API documentation is disabled.")
        return super().dispatch(request, *args, **kwargs)


class NexoraSchemaView(DocsDisabledMixin, SpectacularAPIView):
    pass


class NexoraSwaggerView(DocsDisabledMixin, SpectacularSwaggerView):
    pass


class NexoraRedocView(DocsDisabledMixin, SpectacularRedocView):
    pass


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("config.api.v1.urls")),
    path("api/schema/", NexoraSchemaView.as_view(), name="schema"),
    path("api/docs/", NexoraSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", NexoraRedocView.as_view(url_name="schema"), name="redoc"),
]
