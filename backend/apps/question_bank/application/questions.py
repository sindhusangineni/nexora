import uuid
from typing import Any, Sequence

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

from apps.learning.models import Topic
from apps.question_bank.exceptions import (
    ContentRepresentationError,
    ImmutableVersionError,
    InvalidTopicError,
    QuestionBankError,
    VersionCreationConflictError,
)
from apps.question_bank.models import (
    AssertionReasonContent,
    DescriptiveContent,
    MatchFollowingContent,
    MatchFollowingItem,
    MatchFollowingPair,
    MatchItemSide,
    Question,
    QuestionSourceType,
    QuestionStatus,
    QuestionTopic,
    QuestionType,
    QuestionVersion,
    QuestionVersionChoice,
    TrueFalseContent,
)
from apps.question_bank.validators import validate_single_content_representation


def _validate_and_get_topics(topic_ids: Sequence[str | uuid.UUID]) -> list[Topic]:
    """
    Validate that provided topic identifiers exist and return the Topic instances.
    Raises InvalidTopicError if any topic ID is malformed or not found in Learning.
    """
    if not topic_ids:
        return []

    parsed_ids: list[uuid.UUID] = []
    for tid in topic_ids:
        if isinstance(tid, uuid.UUID):
            parsed_ids.append(tid)
        else:
            try:
                parsed_ids.append(uuid.UUID(str(tid)))
            except (ValueError, AttributeError, TypeError) as err:
                raise InvalidTopicError(
                    f"Invalid topic ID format: '{tid}'. Must be a valid UUID string."
                ) from err

    unique_ids = set(parsed_ids)
    found_topics = list(Topic.objects.filter(id__in=unique_ids))
    if len(found_topics) != len(unique_ids):
        found_ids = {t.id for t in found_topics}
        missing = unique_ids - found_ids
        missing_strs = sorted([str(m) for m in missing])
        raise InvalidTopicError(
            f"One or more topics do not exist: {', '.join(missing_strs)}."
        )

    return found_topics


def _create_type_specific_content(
    version: QuestionVersion,
    *,
    question_type: str,
    content_data: Any = None,
    choices: list[dict] | None = None,
    true_false_data: dict | bool | None = None,
    assertion_reason_data: dict | None = None,
    match_following_data: dict | None = None,
    descriptive_data: dict | None = None,
) -> None:
    """
    Create the type-specific content matching question_type and validate the invariant.
    Rejects incompatible content payloads with ContentRepresentationError.
    """
    # 1. Detect conflicting content payloads
    provided_payloads = []
    if choices is not None or (
        isinstance(content_data, (list, tuple))
        or (isinstance(content_data, dict) and "choices" in content_data)
    ):
        provided_payloads.append("choices")
    if (
        true_false_data is not None
        or (isinstance(content_data, dict) and "answer" in content_data)
        or (isinstance(content_data, bool) and not isinstance(content_data, int))
    ):
        provided_payloads.append("true_false")
    if assertion_reason_data is not None or (
        isinstance(content_data, dict)
        and ("assertion" in content_data or "correct_relationship" in content_data)
    ):
        provided_payloads.append("assertion_reason")
    if match_following_data is not None or (
        isinstance(content_data, dict)
        and ("left_items" in content_data or "pairs" in content_data)
    ):
        provided_payloads.append("match_following")
    if descriptive_data is not None or (
        isinstance(content_data, dict)
        and ("marks" in content_data or "expected_answer" in content_data)
    ):
        provided_payloads.append("descriptive")

    expected_payload_name = {
        QuestionType.MCQ: "choices",
        QuestionType.MULTIPLE_SELECT: "choices",
        QuestionType.TRUE_FALSE: "true_false",
        QuestionType.ASSERTION_REASON: "assertion_reason",
        QuestionType.MATCH_FOLLOWING: "match_following",
        QuestionType.DESCRIPTIVE: "descriptive",
    }.get(question_type)

    for p in provided_payloads:
        if p != expected_payload_name:
            raise ContentRepresentationError(
                f"Incompatible content payload '{p}' provided for question_type '{question_type}'."
            )

    # 2. Dispatch creation by question_type
    if question_type in (QuestionType.MCQ, QuestionType.MULTIPLE_SELECT):
        raw_choices = choices
        if raw_choices is None and content_data is not None:
            if isinstance(content_data, (list, tuple)):
                raw_choices = list(content_data)
            elif isinstance(content_data, dict) and "choices" in content_data:
                raw_choices = content_data["choices"]

        if not raw_choices:
            raise ContentRepresentationError(
                f"QuestionVersion of type '{question_type}' requires a non-empty choices list."
            )

        for idx, c in enumerate(raw_choices):
            if not isinstance(c, dict):
                raise ContentRepresentationError("Each choice must be a dictionary.")
            c_text = c.get("text")
            if c_text is None or not str(c_text).strip():
                raise ValidationError("Choice text cannot be blank.")
            c_pos = c.get("position", idx + 1)
            c_is_correct = bool(c.get("is_correct", False))
            choice_obj = QuestionVersionChoice(
                question_version=version,
                text=c_text,
                position=c_pos,
                is_correct=c_is_correct,
            )
            choice_obj.full_clean()
            choice_obj.save()

    elif question_type == QuestionType.TRUE_FALSE:
        tf_val = true_false_data
        if tf_val is None and content_data is not None:
            tf_val = content_data

        ans = None
        if isinstance(tf_val, bool):
            ans = tf_val
        elif isinstance(tf_val, dict) and "answer" in tf_val:
            ans = tf_val["answer"]

        if ans is None or not isinstance(ans, bool):
            raise ContentRepresentationError(
                "TrueFalseContent requires a boolean 'answer' (True or False)."
            )

        tf_obj = TrueFalseContent(
            question_version=version,
            answer=ans,
        )
        tf_obj.full_clean()
        tf_obj.save()

    elif question_type == QuestionType.ASSERTION_REASON:
        ar_val = assertion_reason_data
        if ar_val is None and content_data is not None:
            ar_val = content_data

        if not isinstance(ar_val, dict):
            raise ContentRepresentationError(
                "AssertionReasonContent requires a dictionary payload."
            )

        assertion = ar_val.get("assertion")
        reason = ar_val.get("reason")
        correct_relationship = ar_val.get("correct_relationship")

        if not assertion or not reason or not correct_relationship:
            raise ContentRepresentationError(
                "AssertionReasonContent requires 'assertion', 'reason', and 'correct_relationship'."
            )

        ar_obj = AssertionReasonContent(
            question_version=version,
            assertion=assertion,
            reason=reason,
            correct_relationship=correct_relationship,
        )
        ar_obj.full_clean()
        ar_obj.save()

    elif question_type == QuestionType.MATCH_FOLLOWING:
        mf_val = match_following_data
        if mf_val is None and content_data is not None:
            mf_val = content_data

        if not isinstance(mf_val, dict):
            raise ContentRepresentationError(
                "MatchFollowingContent requires a dictionary payload containing 'left_items', 'right_items', and 'pairs'."
            )

        left_items = mf_val.get("left_items", [])
        right_items = mf_val.get("right_items", [])
        pairs = mf_val.get("pairs", [])

        if not left_items or not right_items:
            raise ContentRepresentationError(
                "MatchFollowingContent requires non-empty 'left_items' and 'right_items'."
            )

        mf_content = MatchFollowingContent(question_version=version)
        mf_content.full_clean()
        mf_content.save()

        left_map: dict[int, MatchFollowingItem] = {}
        for idx, item in enumerate(left_items):
            pos = item.get("position", idx + 1) if isinstance(item, dict) else (idx + 1)
            txt = item.get("text") if isinstance(item, dict) else str(item)
            item_obj = MatchFollowingItem(
                question_version=version,
                side=MatchItemSide.LEFT,
                text=txt,
                position=pos,
            )
            item_obj.full_clean()
            item_obj.save()
            left_map[pos] = item_obj

        right_map: dict[int, MatchFollowingItem] = {}
        for idx, item in enumerate(right_items):
            pos = item.get("position", idx + 1) if isinstance(item, dict) else (idx + 1)
            txt = item.get("text") if isinstance(item, dict) else str(item)
            item_obj = MatchFollowingItem(
                question_version=version,
                side=MatchItemSide.RIGHT,
                text=txt,
                position=pos,
            )
            item_obj.full_clean()
            item_obj.save()
            right_map[pos] = item_obj

        for pair in pairs:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                l_pos, r_pos = pair[0], pair[1]
            elif isinstance(pair, dict):
                l_pos = pair.get("left_position") if "left_position" in pair else pair.get("left")
                r_pos = pair.get("right_position") if "right_position" in pair else pair.get("right")
            else:
                raise ContentRepresentationError(f"Invalid pair format: '{pair}'.")

            left_item = left_map.get(l_pos)
            right_item = right_map.get(r_pos)
            if not left_item or not right_item:
                raise ContentRepresentationError(
                    f"MatchFollowingPair references non-existent item positions: left={l_pos}, right={r_pos}."
                )

            pair_obj = MatchFollowingPair(
                question_version=version,
                left_item=left_item,
                right_item=right_item,
            )
            pair_obj.full_clean()
            pair_obj.save()

    elif question_type == QuestionType.DESCRIPTIVE:
        desc_val = descriptive_data
        if desc_val is None and content_data is not None:
            desc_val = content_data

        if not isinstance(desc_val, dict):
            raise ContentRepresentationError(
                "DescriptiveContent requires a dictionary payload containing 'marks' and 'expected_answer'."
            )

        marks = desc_val.get("marks")
        expected_answer = desc_val.get("expected_answer", "")

        if marks is None:
            raise ContentRepresentationError("DescriptiveContent requires 'marks'.")

        desc_obj = DescriptiveContent(
            question_version=version,
            marks=marks,
            expected_answer=expected_answer,
        )
        desc_obj.full_clean()
        desc_obj.save()

    # 3. Final domain validation: exactly one type-specific representation
    validate_single_content_representation(version)


@transaction.atomic
def create_question(
    *,
    question_type: str,
    text: str,
    difficulty: str,
    explanation: str = "",
    topic_ids: Sequence[str | uuid.UUID] | None = None,
    # Provenance metadata (Phase 1.1)
    source_type: str | None = None,
    source_name: str | None = None,
    source_reference: str | None = None,
    source_year: int | None = None,
    external_question_id: str | None = None,
    # Type-specific content payloads
    content_data: Any = None,
    choices: list[dict] | None = None,
    true_false_data: dict | bool | None = None,
    assertion_reason_data: dict | None = None,
    match_following_data: dict | None = None,
    descriptive_data: dict | None = None,
) -> Question:
    """
    Atomically creates a new conceptual Question and its initial version (version 1, DRAFT).
    Orchestrates:
    1. Question identity
    2. Topic validation and QuestionTopic associations
    3. QuestionVersion(version_number=1, status=DRAFT)
    4. Type-specific content representation
    5. Provenance metadata
    Rolls back completely if any part fails.
    """
    # 1. Validate topic associations upfront
    topics = _validate_and_get_topics(topic_ids) if topic_ids else []

    if not text or not str(text).strip():
        raise ValidationError("Question text cannot be blank.")

    # 2. Create conceptual Question
    question = Question.objects.create()

    # 3. Create initial QuestionVersion
    version = QuestionVersion(
        question=question,
        version_number=1,
        question_type=question_type,
        text=text,
        difficulty=difficulty,
        explanation=explanation,
        status=QuestionStatus.DRAFT,
        source_type=source_type,
        source_name=source_name,
        source_reference=source_reference,
        source_year=source_year,
        external_question_id=external_question_id,
    )
    version.full_clean()
    version.save()

    # 4. Create type-specific content
    _create_type_specific_content(
        version,
        question_type=question_type,
        content_data=content_data,
        choices=choices,
        true_false_data=true_false_data,
        assertion_reason_data=assertion_reason_data,
        match_following_data=match_following_data,
        descriptive_data=descriptive_data,
    )

    # 5. Create QuestionTopic associations
    for topic in topics:
        QuestionTopic.objects.create(question=question, topic=topic)

    question.initial_version = version
    return question


@transaction.atomic
def create_question_version(
    question: Question | uuid.UUID | str,
    *,
    question_type: str,
    text: str,
    difficulty: str,
    explanation: str = "",
    topic_ids: Sequence[str | uuid.UUID] | None = None,
    # Provenance metadata (Phase 1.1)
    source_type: str | None = None,
    source_name: str | None = None,
    source_reference: str | None = None,
    source_year: int | None = None,
    external_question_id: str | None = None,
    # Type-specific content payloads
    content_data: Any = None,
    choices: list[dict] | None = None,
    true_false_data: dict | bool | None = None,
    assertion_reason_data: dict | None = None,
    match_following_data: dict | None = None,
    descriptive_data: dict | None = None,
) -> QuestionVersion:
    """
    Creates a new editorial version for an existing Question.
    Orchestrates:
    1. Locking the parent Question row with select_for_update() to serialize version numbering.
    2. Calculating next version_number safely.
    3. Ensuring new version starts as DRAFT.
    4. Persisting type-specific content matching question_type.
    5. Syncing QuestionTopic associations if topic_ids is provided.
    6. Translating uniqueness collisions to VersionCreationConflictError.
    """
    q_id = question.id if isinstance(question, Question) else question
    try:
        if isinstance(q_id, str):
            q_id = uuid.UUID(q_id)
    except (ValueError, AttributeError) as err:
        raise QuestionBankError(f"Invalid question ID '{question}'. Must be a valid UUID.") from err

    try:
        question_obj = Question.objects.select_for_update().get(pk=q_id)
    except Question.DoesNotExist:
        raise QuestionBankError(f"Question '{q_id}' does not exist.")

    # Validate topics if specified
    topics = _validate_and_get_topics(topic_ids) if topic_ids is not None else None

    if not text or not str(text).strip():
        raise ValidationError("Question text cannot be blank.")

    # Determine next version number
    max_v = (
        QuestionVersion.objects.filter(question=question_obj)
        .aggregate(m=models.Max("version_number"))
        .get("m")
    )
    next_version_number = (max_v + 1) if max_v is not None else 1

    try:
        version = QuestionVersion(
            question=question_obj,
            version_number=next_version_number,
            question_type=question_type,
            text=text,
            difficulty=difficulty,
            explanation=explanation,
            status=QuestionStatus.DRAFT,
            source_type=source_type,
            source_name=source_name,
            source_reference=source_reference,
            source_year=source_year,
            external_question_id=external_question_id,
        )
        version.full_clean()
        version.save()

        _create_type_specific_content(
            version,
            question_type=question_type,
            content_data=content_data,
            choices=choices,
            true_false_data=true_false_data,
            assertion_reason_data=assertion_reason_data,
            match_following_data=match_following_data,
            descriptive_data=descriptive_data,
        )

        if topics is not None:
            existing_topics = {qt.topic_id: qt for qt in question_obj.question_topics.all()}
            new_ids = {t.id for t in topics}
            for tid, qt in existing_topics.items():
                if tid not in new_ids:
                    qt.delete()
            for topic in topics:
                if topic.id not in existing_topics:
                    QuestionTopic.objects.create(question=question_obj, topic=topic)

    except IntegrityError as exc:
        if "unique_question_version_number" in str(exc):
            raise VersionCreationConflictError(
                f"Concurrent version creation conflict for question {question_obj.id} at version {next_version_number}."
            ) from exc
        raise

    return version


_UNSET = object()


@transaction.atomic
def update_question_version(
    version_id: uuid.UUID | str,
    *,
    text: str | object = _UNSET,
    difficulty: str | object = _UNSET,
    explanation: str | object = _UNSET,
    topic_ids: Sequence[str | uuid.UUID] | None | object = _UNSET,
    source_type: str | None | object = _UNSET,
    source_name: str | None | object = _UNSET,
    source_reference: str | None | object = _UNSET,
    source_year: int | None | object = _UNSET,
    external_question_id: str | None | object = _UNSET,
    choices: list[dict] | None = None,
    true_false_data: dict | bool | None = None,
    assertion_reason_data: dict | None = None,
    match_following_data: dict | None = None,
    descriptive_data: dict | None = None,
) -> QuestionVersion:
    """
    Atomically updates editable fields of a DRAFT QuestionVersion.
    Enforces:
    1. Version must exist and have status == DRAFT.
    2. Modifying immutable versions (REVIEW, APPROVED, PUBLISHED, ARCHIVED) is rejected.
    3. Immutable attributes (version_number, status, question_type, question identity) cannot be altered.
    4. Type-specific content updates must strictly match version.question_type.
    5. Topics can be updated on the conceptual Question if topic_ids is provided.
    6. Ensures type invariant is maintained via validate_single_content_representation.
    """
    v_id = version_id if isinstance(version_id, uuid.UUID) else uuid.UUID(str(version_id))

    try:
        version = QuestionVersion.objects.select_for_update().get(pk=v_id)
    except QuestionVersion.DoesNotExist:
        raise QuestionBankError(f"QuestionVersion '{v_id}' does not exist.")

    if version.status != QuestionStatus.DRAFT:
        raise ImmutableVersionError(
            f"Cannot edit question version with status '{version.status}'. Only DRAFT versions may be edited."
        )

    # 1. Update basic version fields
    if text is not _UNSET:
        if not text or not str(text).strip():
            raise ValidationError("Question text cannot be blank.")
        version.text = str(text).strip()

    if difficulty is not _UNSET and difficulty is not None:
        version.difficulty = difficulty

    if explanation is not _UNSET:
        version.explanation = explanation or ""

    # 2. Update provenance metadata
    if source_type is not _UNSET:
        version.source_type = source_type
    if source_name is not _UNSET:
        version.source_name = source_name
    if source_reference is not _UNSET:
        version.source_reference = source_reference
    if source_year is not _UNSET:
        version.source_year = source_year
    if external_question_id is not _UNSET:
        version.external_question_id = external_question_id

    # 3. Update topics if explicitly passed
    if topic_ids is not _UNSET and topic_ids is not None:
        topics = _validate_and_get_topics(topic_ids)
        question_obj = version.question
        existing_topics = {qt.topic_id: qt for qt in question_obj.question_topics.all()}
        new_ids = {t.id for t in topics}
        for tid, qt in existing_topics.items():
            if tid not in new_ids:
                qt.delete()
        for topic in topics:
            if topic.id not in existing_topics:
                QuestionTopic.objects.create(question=question_obj, topic=topic)

    # 4. Update type-specific content
    has_content_update = any(
        x is not None
        for x in (choices, true_false_data, assertion_reason_data, match_following_data, descriptive_data)
    )
    if has_content_update:
        q_type = version.question_type

        if choices is not None:
            if q_type not in (QuestionType.MCQ, QuestionType.MULTIPLE_SELECT):
                raise ContentRepresentationError("Cannot update choices for non-choice question type.")
            version.choices.all().delete()
            for idx, c in enumerate(choices):
                if not isinstance(c, dict):
                    raise ContentRepresentationError("Each choice must be a dictionary.")
                c_text = c.get("text")
                if c_text is None or not str(c_text).strip():
                    raise ValidationError("Choice text cannot be blank.")
                c_pos = c.get("position", idx + 1)
                c_is_correct = bool(c.get("is_correct", False))
                choice_obj = QuestionVersionChoice(
                    question_version=version,
                    text=c_text,
                    position=c_pos,
                    is_correct=c_is_correct,
                )
                choice_obj.full_clean()
                choice_obj.save()

        elif true_false_data is not None:
            if q_type != QuestionType.TRUE_FALSE:
                raise ContentRepresentationError("Cannot update true_false for non-TF question type.")
            ans = None
            if isinstance(true_false_data, bool):
                ans = true_false_data
            elif isinstance(true_false_data, dict) and "answer" in true_false_data:
                ans = true_false_data["answer"]
            if ans is None or not isinstance(ans, bool):
                raise ContentRepresentationError("TrueFalseContent requires a boolean 'answer'.")
            tf_obj = TrueFalseContent.objects.filter(question_version=version).first()
            if tf_obj:
                tf_obj.answer = ans
                tf_obj.full_clean()
                tf_obj.save()
            else:
                tf_new = TrueFalseContent(question_version=version, answer=ans)
                tf_new.full_clean()
                tf_new.save()

        elif assertion_reason_data is not None:
            if q_type != QuestionType.ASSERTION_REASON:
                raise ContentRepresentationError("Cannot update assertion_reason for non-AR question type.")
            if not isinstance(assertion_reason_data, dict):
                raise ContentRepresentationError("AssertionReasonContent requires a dictionary payload.")
            assertion = assertion_reason_data.get("assertion")
            reason = assertion_reason_data.get("reason")
            correct_relationship = assertion_reason_data.get("correct_relationship")
            if not assertion or not reason or not correct_relationship:
                raise ContentRepresentationError(
                    "AssertionReasonContent requires 'assertion', 'reason', and 'correct_relationship'."
                )
            ar_obj = AssertionReasonContent.objects.filter(question_version=version).first()
            if ar_obj:
                ar_obj.assertion = assertion
                ar_obj.reason = reason
                ar_obj.correct_relationship = correct_relationship
                ar_obj.full_clean()
                ar_obj.save()
            else:
                ar_new = AssertionReasonContent(
                    question_version=version,
                    assertion=assertion,
                    reason=reason,
                    correct_relationship=correct_relationship,
                )
                ar_new.full_clean()
                ar_new.save()

        elif match_following_data is not None:
            if q_type != QuestionType.MATCH_FOLLOWING:
                raise ContentRepresentationError("Cannot update match_following for non-MF question type.")
            if not isinstance(match_following_data, dict):
                raise ContentRepresentationError("MatchFollowingContent requires a dictionary payload.")
            version.match_pairs.all().delete()
            version.match_items.all().delete()
            MatchFollowingContent.objects.get_or_create(question_version=version)

            left_items = match_following_data.get("left_items", [])
            right_items = match_following_data.get("right_items", [])
            pairs = match_following_data.get("pairs", [])

            if not left_items or not right_items:
                raise ContentRepresentationError(
                    "MatchFollowingContent requires non-empty 'left_items' and 'right_items'."
                )

            left_map = {}
            for idx, it in enumerate(left_items):
                pos = it.get("position", idx + 1) if isinstance(it, dict) else (idx + 1)
                txt = it.get("text") if isinstance(it, dict) else str(it)
                item_obj = MatchFollowingItem(
                    question_version=version,
                    side=MatchItemSide.LEFT,
                    text=txt,
                    position=pos,
                )
                item_obj.full_clean()
                item_obj.save()
                left_map[pos] = item_obj

            right_map = {}
            for idx, it in enumerate(right_items):
                pos = it.get("position", idx + 1) if isinstance(it, dict) else (idx + 1)
                txt = it.get("text") if isinstance(it, dict) else str(it)
                item_obj = MatchFollowingItem(
                    question_version=version,
                    side=MatchItemSide.RIGHT,
                    text=txt,
                    position=pos,
                )
                item_obj.full_clean()
                item_obj.save()
                right_map[pos] = item_obj

            for pair in pairs:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    l_pos, r_pos = pair[0], pair[1]
                elif isinstance(pair, dict):
                    l_pos = pair.get("left_position") if "left_position" in pair else pair.get("left")
                    r_pos = pair.get("right_position") if "right_position" in pair else pair.get("right")
                else:
                    raise ContentRepresentationError(f"Invalid pair format: '{pair}'.")

                left_item = left_map.get(l_pos)
                right_item = right_map.get(r_pos)
                if not left_item or not right_item:
                    raise ContentRepresentationError(
                        f"MatchFollowingPair references non-existent item positions: left={l_pos}, right={r_pos}."
                    )
                pair_obj = MatchFollowingPair(
                    question_version=version,
                    left_item=left_item,
                    right_item=right_item,
                )
                pair_obj.full_clean()
                pair_obj.save()

        elif descriptive_data is not None:
            if q_type != QuestionType.DESCRIPTIVE:
                raise ContentRepresentationError("Cannot update descriptive for non-descriptive question type.")
            if not isinstance(descriptive_data, dict):
                raise ContentRepresentationError("DescriptiveContent requires a dictionary payload.")
            marks = descriptive_data.get("marks")
            expected_answer = descriptive_data.get("expected_answer", "")
            if marks is None:
                raise ContentRepresentationError("DescriptiveContent requires 'marks'.")
            desc_obj = DescriptiveContent.objects.filter(question_version=version).first()
            if desc_obj:
                desc_obj.marks = marks
                desc_obj.expected_answer = expected_answer
                desc_obj.full_clean()
                desc_obj.save()
            else:
                desc_new = DescriptiveContent(
                    question_version=version,
                    marks=marks,
                    expected_answer=expected_answer,
                )
                desc_new.full_clean()
                desc_new.save()

    # 5. Invariant validation and full clean
    validate_single_content_representation(version)
    version.full_clean()
    version.save()

    return version

