from uuid import UUID
from django.db import transaction

from apps.assessment.exceptions import AssessmentNotFoundError
from apps.assessment.models import Assessment


@transaction.atomic
def publish_assessment(assessment_id: UUID) -> Assessment:
    """
    Publishes a DRAFT assessment, validating its configuration and selection rules.
    """
    assessment = (
        Assessment.objects.select_for_update()
        .filter(id=assessment_id)
        .first()
    )
    if not assessment:
        raise AssessmentNotFoundError("Assessment not found.")

    assessment.publish()
    return assessment


@transaction.atomic
def archive_assessment(assessment_id: UUID) -> Assessment:
    """
    Archives a PUBLISHED assessment, making it permanently read-only.
    """
    assessment = (
        Assessment.objects.select_for_update()
        .filter(id=assessment_id)
        .first()
    )
    if not assessment:
        raise AssessmentNotFoundError("Assessment not found.")

    assessment.archive()
    return assessment
