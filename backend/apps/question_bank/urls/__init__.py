from django.urls import path

from apps.question_bank.views import (
    QuestionImportViewSet,
    QuestionVersionViewSet,
    QuestionViewSet,
)

question_list = QuestionViewSet.as_view({
    "get": "list",
    "post": "create",
})
question_detail = QuestionViewSet.as_view({
    "get": "retrieve",
})

version_list = QuestionVersionViewSet.as_view({
    "get": "list",
    "post": "create",
})
version_detail = QuestionVersionViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
})
version_submit_review = QuestionVersionViewSet.as_view({
    "post": "submit_review",
})
version_approve = QuestionVersionViewSet.as_view({
    "post": "approve",
})
version_publish = QuestionVersionViewSet.as_view({
    "post": "publish",
})
version_archive = QuestionVersionViewSet.as_view({
    "post": "archive",
})

import_preview = QuestionImportViewSet.as_view({
    "post": "preview",
})
import_execute = QuestionImportViewSet.as_view({
    "post": "execute",
})
import_template = QuestionImportViewSet.as_view({
    "get": "template",
})

urlpatterns = [
    # Bulk import endpoints
    path("imports/preview/", import_preview, name="question-import-preview"),
    path("imports/execute/", import_execute, name="question-import-execute"),
    path("imports/template/", import_template, name="question-import-template"),
    # Question aggregates
    path("questions/", question_list, name="question-list"),
    path("questions/<uuid:question_id>/", question_detail, name="question-detail"),
    path(
        "questions/<uuid:question_id>/versions/",
        version_list,
        name="question-version-list",
    ),
    path(
        "questions/<uuid:question_id>/versions/<uuid:version_id>/",
        version_detail,
        name="question-version-detail",
    ),
    path(
        "questions/<uuid:question_id>/versions/<uuid:version_id>/submit-review/",
        version_submit_review,
        name="question-version-submit-review",
    ),
    path(
        "questions/<uuid:question_id>/versions/<uuid:version_id>/approve/",
        version_approve,
        name="question-version-approve",
    ),
    path(
        "questions/<uuid:question_id>/versions/<uuid:version_id>/publish/",
        version_publish,
        name="question-version-publish",
    ),
    path(
        "questions/<uuid:question_id>/versions/<uuid:version_id>/archive/",
        version_archive,
        name="question-version-archive",
    ),
]
