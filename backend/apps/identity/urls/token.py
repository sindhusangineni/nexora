from django.urls import path

from apps.identity.views.token import TokenRefreshView

urlpatterns = [
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
