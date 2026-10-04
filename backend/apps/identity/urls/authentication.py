from django.urls import path

from apps.identity.views.authentication import LoginView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
]
