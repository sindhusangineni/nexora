from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.identity.urls")),
    path("learning/", include("apps.learning.urls")),
]
