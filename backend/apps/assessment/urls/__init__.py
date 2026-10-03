from django.urls import path

from apps.assessment.views import (
    AssessmentArchiveView,
    AssessmentDetailView,
    AssessmentListCreateView,
    AssessmentPaperDetailView,
    AssessmentPublishView,
    AssessmentSectionDetailView,
    AssessmentSectionListCreateView,
    GeneratePaperView,
    SelectionRuleDetailView,
    SelectionRuleListCreateView,
)

urlpatterns = [
    # Assessment definitions & lifecycle
    path("assessments/", AssessmentListCreateView.as_view(), name="assessment-list-create"),
    path("assessments/<uuid:assessment_id>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("assessments/<uuid:assessment_id>/publish/", AssessmentPublishView.as_view(), name="assessment-publish"),
    path("assessments/<uuid:assessment_id>/archive/", AssessmentArchiveView.as_view(), name="assessment-archive"),

    # Sections
    path("assessments/<uuid:assessment_id>/sections/", AssessmentSectionListCreateView.as_view(), name="assessment-section-list-create"),
    path("sections/<uuid:section_id>/", AssessmentSectionDetailView.as_view(), name="assessment-section-detail"),

    # Selection rules
    path("assessments/<uuid:assessment_id>/rules/", SelectionRuleListCreateView.as_view(), name="assessment-rule-list-create"),
    path("rules/<uuid:rule_id>/", SelectionRuleDetailView.as_view(), name="assessment-rule-detail"),

    # Paper generation & retrieval
    path("assessments/<uuid:assessment_id>/generate-paper/", GeneratePaperView.as_view(), name="assessment-generate-paper"),
    path("papers/<uuid:paper_id>/", AssessmentPaperDetailView.as_view(), name="assessment-paper-detail"),
]
