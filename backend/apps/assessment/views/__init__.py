from apps.assessment.views.assessments import (
    AssessmentArchiveView,
    AssessmentDetailView,
    AssessmentListCreateView,
    AssessmentPublishView,
)
from apps.assessment.views.papers import (
    AssessmentPaperDetailView,
    GeneratePaperView,
)
from apps.assessment.views.rules import (
    SelectionRuleDetailView,
    SelectionRuleListCreateView,
)
from apps.assessment.views.sections import (
    AssessmentSectionDetailView,
    AssessmentSectionListCreateView,
)

__all__ = [
    "AssessmentListCreateView",
    "AssessmentDetailView",
    "AssessmentPublishView",
    "AssessmentArchiveView",
    "AssessmentSectionListCreateView",
    "AssessmentSectionDetailView",
    "SelectionRuleListCreateView",
    "SelectionRuleDetailView",
    "GeneratePaperView",
    "AssessmentPaperDetailView",
]
