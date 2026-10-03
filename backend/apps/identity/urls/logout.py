from django.urls import path

from apps.identity.views.logout import LogoutView

urlpatterns = [
    path("logout/", LogoutView.as_view(), name="logout"),
]
