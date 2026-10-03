from django.urls import path

from apps.identity.views.registration import RegistrationView

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
]
