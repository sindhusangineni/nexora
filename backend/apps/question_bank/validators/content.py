from django.apps import apps

from apps.question_bank.exceptions import ContentRepresentationError
from apps.question_bank.models.enums import QuestionType


def validate_single_content_representation(version) -> None:
    """
    Ensure that a QuestionVersion has exactly one type-specific content representation
    corresponding to its question_type:
    - MCQ / MULTIPLE_SELECT -> QuestionVersionChoice representation
    - TRUE_FALSE -> TrueFalseContent
    - ASSERTION_REASON -> AssertionReasonContent
    - MATCH_FOLLOWING -> MatchFollowingContent
    - DESCRIPTIVE -> DescriptiveContent

    Structural validity requires:
    1. Not zero representations (the required type-specific representation must exist).
    2. Exactly one type-specific representation (no multiple or conflicting representations).
    3. No representations belonging to another question type.

    Raises ContentRepresentationError if structurally invalid.
    """
    q_type = version.question_type

    TrueFalseContent = apps.get_model("question_bank", "TrueFalseContent")
    AssertionReasonContent = apps.get_model("question_bank", "AssertionReasonContent")
    MatchFollowingContent = apps.get_model("question_bank", "MatchFollowingContent")
    DescriptiveContent = apps.get_model("question_bank", "DescriptiveContent")

    has_choices = version.choices.exists() if version.pk else False
    has_tf = (
        TrueFalseContent.objects.filter(question_version_id=version.pk).exists()
        if version.pk
        else False
    )
    has_ar = (
        AssertionReasonContent.objects.filter(question_version_id=version.pk).exists()
        if version.pk
        else False
    )
    has_mf = (
        MatchFollowingContent.objects.filter(question_version_id=version.pk).exists()
        if version.pk
        else False
    )
    has_desc = (
        DescriptiveContent.objects.filter(question_version_id=version.pk).exists()
        if version.pk
        else False
    )

    present_representations: list[str] = []
    if has_choices:
        present_representations.append("choices")
    if has_tf:
        present_representations.append("true_false_content")
    if has_ar:
        present_representations.append("assertion_reason_content")
    if has_mf:
        present_representations.append("match_following_content")
    if has_desc:
        present_representations.append("descriptive_content")

    # 1. Zero representations check
    if not present_representations:
        raise ContentRepresentationError(
            f"QuestionVersion of type '{q_type}' has no content representation. "
            f"Exactly one type-specific representation is required."
        )

    # 2. Expected representation check
    expected_rep = {
        QuestionType.MCQ: "choices",
        QuestionType.MULTIPLE_SELECT: "choices",
        QuestionType.TRUE_FALSE: "true_false_content",
        QuestionType.ASSERTION_REASON: "assertion_reason_content",
        QuestionType.MATCH_FOLLOWING: "match_following_content",
        QuestionType.DESCRIPTIVE: "descriptive_content",
    }.get(q_type)

    if expected_rep not in present_representations:
        raise ContentRepresentationError(
            f"QuestionVersion of type '{q_type}' is missing required representation '{expected_rep}'. "
            f"Found: {present_representations}."
        )

    # 3. Multiple / Incompatible representations check
    if len(present_representations) > 1:
        extraneous = [r for r in present_representations if r != expected_rep]
        raise ContentRepresentationError(
            f"QuestionVersion of type '{q_type}' has multiple incompatible content representations. "
            f"Expected only '{expected_rep}', but also found {extraneous}."
        )
