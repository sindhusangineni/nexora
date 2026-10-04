from rest_framework import serializers

from apps.question_bank.models import (
    MatchItemSide,
    Question,
    QuestionType,
    QuestionVersion,
)


class QuestionVersionAdminResponseSerializer(serializers.ModelSerializer):
    """
    Complete editorial response representation of a QuestionVersion for administrators.
    Exposes full editorial lifecycle, correct answers, and provenance metadata.
    """

    question_id = serializers.UUIDField(read_only=True)
    content = serializers.SerializerMethodField(
        help_text="Type-specific structured content payload including correct answers/rubrics.",
    )

    class Meta:
        model = QuestionVersion
        fields = [
            "id",
            "question_id",
            "version_number",
            "question_type",
            "difficulty",
            "status",
            "text",
            "explanation",
            "source_type",
            "source_name",
            "source_reference",
            "source_year",
            "external_question_id",
            "content",
            "created_at",
            "updated_at",
        ]

    def get_content(self, obj: QuestionVersion) -> dict:
        q_type = obj.question_type

        if q_type in (QuestionType.MCQ, QuestionType.MULTIPLE_SELECT):
            choices = obj.choices.order_by("position")
            return {
                "choices": [
                    {
                        "id": str(c.id),
                        "text": c.text,
                        "position": c.position,
                        "is_correct": c.is_correct,
                    }
                    for c in choices
                ]
            }

        elif q_type == QuestionType.TRUE_FALSE:
            tf = getattr(obj, "true_false_content", None)
            return {"answer": tf.answer if tf else None}

        elif q_type == QuestionType.ASSERTION_REASON:
            ar = getattr(obj, "assertion_reason_content", None)
            if not ar:
                return {}
            return {
                "assertion": ar.assertion,
                "reason": ar.reason,
                "correct_relationship": ar.correct_relationship,
            }

        elif q_type == QuestionType.MATCH_FOLLOWING:
            left_items = obj.match_items.filter(side=MatchItemSide.LEFT).order_by("position")
            right_items = obj.match_items.filter(side=MatchItemSide.RIGHT).order_by("position")
            pairs = obj.match_pairs.all()
            return {
                "left_items": [
                    {"id": str(i.id), "text": i.text, "position": i.position}
                    for i in left_items
                ],
                "right_items": [
                    {"id": str(i.id), "text": i.text, "position": i.position}
                    for i in right_items
                ],
                "pairs": [
                    {
                        "left_position": p.left_item.position,
                        "right_position": p.right_item.position,
                    }
                    for p in pairs
                ],
            }

        elif q_type == QuestionType.DESCRIPTIVE:
            desc = getattr(obj, "descriptive_content", None)
            if not desc:
                return {}
            return {
                "marks": desc.marks,
                "expected_answer": desc.expected_answer,
            }

        return {}


class QuestionAdminResponseSerializer(serializers.ModelSerializer):
    """
    Authoring response representation of a Question aggregate for administrators.
    """

    topic_ids = serializers.SerializerMethodField(
        help_text="List of associated Learning Topic UUIDs.",
    )
    latest_version = QuestionVersionAdminResponseSerializer(
        read_only=True,
        help_text="The latest editorial version of this question.",
    )
    published_version = QuestionVersionAdminResponseSerializer(
        read_only=True,
        help_text="The currently published version of this question, if any.",
    )
    version_count = serializers.SerializerMethodField(
        help_text="Total count of editorial versions for this question.",
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "topic_ids",
            "latest_version",
            "published_version",
            "version_count",
            "created_at",
            "updated_at",
        ]

    def get_topic_ids(self, obj: Question) -> list[str]:
        return [str(qt.topic_id) for qt in obj.question_topics.all()]

    def get_version_count(self, obj: Question) -> int:
        return obj.versions.count()


class QuestionVersionStudentResponseSerializer(serializers.ModelSerializer):
    """
    Sanitized response representation of a published QuestionVersion for students.
    Strictly omits correct answers, internal editorial statuses, and provenance.
    """

    question_id = serializers.UUIDField(read_only=True)
    content = serializers.SerializerMethodField(
        help_text="Sanitized question content without answer keys or evaluation rubrics.",
    )

    class Meta:
        model = QuestionVersion
        fields = [
            "id",
            "question_id",
            "version_number",
            "question_type",
            "difficulty",
            "text",
            "content",
        ]

    def get_content(self, obj: QuestionVersion) -> dict:
        q_type = obj.question_type

        if q_type in (QuestionType.MCQ, QuestionType.MULTIPLE_SELECT):
            choices = obj.choices.order_by("position")
            return {
                "choices": [
                    {
                        "id": str(c.id),
                        "text": c.text,
                        "position": c.position,
                        # is_correct is intentionally OMITTED for students
                    }
                    for c in choices
                ]
            }

        elif q_type == QuestionType.TRUE_FALSE:
            # answer is intentionally OMITTED for students
            return {}

        elif q_type == QuestionType.ASSERTION_REASON:
            ar = getattr(obj, "assertion_reason_content", None)
            if not ar:
                return {}
            return {
                "assertion": ar.assertion,
                "reason": ar.reason,
                # correct_relationship is intentionally OMITTED for students
            }

        elif q_type == QuestionType.MATCH_FOLLOWING:
            left_items = obj.match_items.filter(side=MatchItemSide.LEFT).order_by("position")
            right_items = obj.match_items.filter(side=MatchItemSide.RIGHT).order_by("position")
            # pairs are intentionally OMITTED for students
            return {
                "left_items": [
                    {"id": str(i.id), "text": i.text, "position": i.position}
                    for i in left_items
                ],
                "right_items": [
                    {"id": str(i.id), "text": i.text, "position": i.position}
                    for i in right_items
                ],
            }

        elif q_type == QuestionType.DESCRIPTIVE:
            desc = getattr(obj, "descriptive_content", None)
            if not desc:
                return {}
            return {
                "marks": desc.marks,
                # expected_answer rubric is intentionally OMITTED for students
            }

        return {}


class QuestionStudentResponseSerializer(serializers.ModelSerializer):
    """
    Sanitized response representation of a Question aggregate for students.
    Only exposes published content.
    """

    topic_ids = serializers.SerializerMethodField(
        help_text="List of associated Learning Topic UUIDs.",
    )
    published_version = QuestionVersionStudentResponseSerializer(
        read_only=True,
        help_text="The published version accessible to students.",
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "topic_ids",
            "published_version",
        ]

    def get_topic_ids(self, obj: Question) -> list[str]:
        return [str(qt.topic_id) for qt in obj.question_topics.all()]
