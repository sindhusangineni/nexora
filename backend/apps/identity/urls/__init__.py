from django.urls import include, path

app_name = "identity"

urlpatterns = [
    path("", include("apps.identity.urls.registration")),
    path("", include("apps.identity.urls.authentication")),
    path("", include("apps.identity.urls.token")),
    path("", include("apps.identity.urls.logout")),
]
