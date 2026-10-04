from django.urls import path

from apps.attempts.views import (
    AttemptCancelView,
    AttemptDetailView,
    AttemptItemEvaluateView,
    AttemptItemResponseView,
    AttemptListCreateView,
    AttemptResultView,
    AttemptReviewView,
    AttemptSubmitView,
)

urlpatterns = [
    # Student endpoints
    path("", AttemptListCreateView.as_view(), name="attempt-list-create"),
    path("<uuid:attempt_id>/", AttemptDetailView.as_view(), name="attempt-detail"),
    path("<uuid:attempt_id>/submit/", AttemptSubmitView.as_view(), name="attempt-submit"),
    path("<uuid:attempt_id>/result/", AttemptResultView.as_view(), name="attempt-result"),
    path(
        "<uuid:attempt_id>/items/<uuid:item_id>/response/",
        AttemptItemResponseView.as_view(),
        name="attempt-item-response",
    ),

    # Superadmin endpoints
    path(
        "<uuid:attempt_id>/items/<uuid:item_id>/evaluate/",
        AttemptItemEvaluateView.as_view(),
        name="attempt-item-evaluate",
    ),
    path("<uuid:attempt_id>/cancel/", AttemptCancelView.as_view(), name="attempt-cancel"),
    path("<uuid:attempt_id>/review/", AttemptReviewView.as_view(), name="attempt-review"),
]
