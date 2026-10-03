from django.db import transaction

from apps.question_bank.models.enums import QuestionStatus
from apps.question_bank.validators import (
    validate_single_content_representation,
    validate_status_transition,
    validate_version_for_publication,
)


@transaction.atomic
def transition_question_version_status(version, target_status: str):
    """
    Domain service to transition a QuestionVersion's status through its lifecycle.
    Enforces lifecycle transition rules and runs publication validation if moving to PUBLISHED.
    """
    validate_status_transition(version.status, target_status)

    if target_status == QuestionStatus.PUBLISHED:
        validate_single_content_representation(version)
        validate_version_for_publication(version)

    version.status = target_status
    version.save()
    return version
