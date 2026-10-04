from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.identity.urls")),
    path("learning/", include("apps.learning.urls")),
    path("question-bank/", include("apps.question_bank.urls")),
    path("assessment/", include("apps.assessment.urls")),
    path("attempts/", include("apps.attempts.urls")),
]
