from apps.question_bank.exceptions import PublicationValidationError
from apps.question_bank.models.enums import (
    AssertionReasonRelationship,
    Difficulty,
    MatchItemSide,
    QuestionType,
)


def validate_version_for_publication(version) -> None:
    """
    Validate that a QuestionVersion meets all domain publication criteria before
    transitioning to the PUBLISHED status.
    Raises PublicationValidationError if any criterion is unmet.
    """
    errors = []

    # 1. Common checks
    if not version.text or not version.text.strip():
        errors.append("Question text cannot be empty for publication.")

    if not version.difficulty or version.difficulty not in Difficulty.values:
        errors.append("A valid difficulty level must be set for publication.")

    if not version.question_type or version.question_type not in QuestionType.values:
        errors.append("A valid question type must be set for publication.")

    # Topic association check (Question must have at least one Topic)
    if not version.question.question_topics.exists():
        errors.append("The question must be associated with at least one Learning Topic before publication.")

    # 2. Type-specific checks
    q_type = version.question_type

    if q_type == QuestionType.MCQ:
        choices = list(version.choices.all())
        if len(choices) < 2:
            errors.append("MCQ questions require at least 2 choices.")
        correct_count = sum(1 for c in choices if c.is_correct)
        if correct_count != 1:
            errors.append(f"MCQ questions require exactly 1 correct choice, found {correct_count}.")

    elif q_type == QuestionType.MULTIPLE_SELECT:
        choices = list(version.choices.all())
        if len(choices) < 2:
            errors.append("Multiple-select questions require at least 2 choices.")
        correct_count = sum(1 for c in choices if c.is_correct)
        if correct_count < 1:
            errors.append("Multiple-select questions require at least 1 correct choice.")

    elif q_type == QuestionType.TRUE_FALSE:
        tf_content = getattr(version, "true_false_content", None)
        if tf_content is None:
            errors.append("True/False questions require TrueFalseContent.")
        elif tf_content.answer not in (True, False):
            errors.append("True/False questions require a valid boolean answer.")

    elif q_type == QuestionType.ASSERTION_REASON:
        ar_content = getattr(version, "assertion_reason_content", None)
        if ar_content is None:
            errors.append("Assertion/Reason questions require AssertionReasonContent.")
        else:
            if not ar_content.assertion or not ar_content.assertion.strip():
                errors.append("Assertion text cannot be empty.")
            if not ar_content.reason or not ar_content.reason.strip():
                errors.append("Reason text cannot be empty.")
            if ar_content.correct_relationship not in AssertionReasonRelationship.values:
                errors.append("A valid semantic relationship must be selected for Assertion/Reason.")

    elif q_type == QuestionType.MATCH_FOLLOWING:
        mf_content = getattr(version, "match_following_content", None)
        if mf_content is None:
            errors.append("Match Following questions require MatchFollowingContent.")
        else:
            left_items = list(version.match_items.filter(side=MatchItemSide.LEFT))
            right_items = list(version.match_items.filter(side=MatchItemSide.RIGHT))

            if len(left_items) < 2:
                errors.append("Match Following questions require at least 2 LEFT items.")
            if len(right_items) < 2:
                errors.append("Match Following questions require at least 2 RIGHT items.")
            if len(left_items) != len(right_items):
                errors.append(
                    f"Match Following items count mismatch: {len(left_items)} LEFT vs {len(right_items)} RIGHT items."
                )

            pairs = list(version.match_pairs.all())
            expected_pair_count = len(left_items)
            if len(pairs) != expected_pair_count:
                errors.append(
                    f"Match Following requires {expected_pair_count} pairs matching all items, found {len(pairs)}."
                )

            left_ids_in_pairs = {p.left_item_id for p in pairs}
            right_ids_in_pairs = {p.right_item_id for p in pairs}
            all_left_ids = {item.id for item in left_items}
            all_right_ids = {item.id for item in right_items}

            if left_ids_in_pairs != all_left_ids:
                errors.append("Each LEFT item must be mapped exactly once in the pairs.")
            if right_ids_in_pairs != all_right_ids:
                errors.append("Each RIGHT item must be mapped exactly once in the pairs.")

    elif q_type == QuestionType.DESCRIPTIVE:
        desc_content = getattr(version, "descriptive_content", None)
        if desc_content is None:
            errors.append("Descriptive questions require DescriptiveContent.")
        else:
            if not desc_content.marks or desc_content.marks <= 0:
                errors.append("Descriptive questions require marks > 0.")
            if not desc_content.expected_answer or not desc_content.expected_answer.strip():
                errors.append("Descriptive questions require a non-empty expected answer for publication.")

    if errors:
        raise PublicationValidationError(" ".join(errors))
