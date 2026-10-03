from rest_framework import serializers

from apps.question_bank.models.enums import AssertionReasonRelationship


class ChoiceItemRequestSerializer(serializers.Serializer):
    text = serializers.CharField(
        required=True,
        min_length=1,
        help_text="Choice text content.",
    )
    position = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="1-based visual ordering position. Auto-assigned if omitted.",
    )
    is_correct = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Indicates whether this choice is correct.",
    )


class TrueFalseContentRequestSerializer(serializers.Serializer):
    answer = serializers.BooleanField(
        required=True,
        help_text="Correct boolean answer (true or false).",
    )


class AssertionReasonContentRequestSerializer(serializers.Serializer):
    assertion = serializers.CharField(
        required=False,
        min_length=1,
        help_text="The assertion statement.",
    )
    assertion_text = serializers.CharField(
        required=False,
        min_length=1,
        help_text="Alias for assertion statement.",
    )
    reason = serializers.CharField(
        required=False,
        min_length=1,
        help_text="The reason statement explaining the assertion.",
    )
    reason_text = serializers.CharField(
        required=False,
        min_length=1,
        help_text="Alias for reason statement.",
    )
    correct_relationship = serializers.ChoiceField(
        choices=AssertionReasonRelationship.choices,
        required=False,
        help_text="Semantic relationship category.",
    )
    assertion_true = serializers.BooleanField(
        required=False,
        help_text="Whether the assertion statement is factually true.",
    )
    reason_true = serializers.BooleanField(
        required=False,
        help_text="Whether the reason statement is factually true.",
    )
    reason_explains_assertion = serializers.BooleanField(
        required=False,
        help_text="Whether the reason correctly explains the assertion.",
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            allowed = {
                "assertion",
                "assertion_text",
                "reason",
                "reason_text",
                "correct_relationship",
                "assertion_true",
                "reason_true",
                "reason_explains_assertion",
            }
            unknown = set(data.keys()) - allowed
            if unknown:
                raise serializers.ValidationError(
                    f"Unsupported fields in assertion_reason content: {sorted(list(unknown))}."
                )
        return super().to_internal_value(data)

    def validate(self, attrs):

        assertion = attrs.get("assertion") or attrs.get("assertion_text")
        if not assertion:
            raise serializers.ValidationError(
                {"assertion": ["Assertion statement is required ('assertion' or 'assertion_text')."]}
            )

        reason = attrs.get("reason") or attrs.get("reason_text")
        if not reason:
            raise serializers.ValidationError(
                {"reason": ["Reason statement is required ('reason' or 'reason_text')."]}
            )

        has_booleans = "assertion_true" in attrs and "reason_true" in attrs
        has_relationship = "correct_relationship" in attrs

        if not has_booleans and not has_relationship:
            raise serializers.ValidationError(
                "Either 'correct_relationship' or ('assertion_true', 'reason_true') must be provided."
            )

        derived_relationship = None
        if has_booleans:
            a_true = attrs["assertion_true"]
            r_true = attrs["reason_true"]
            explains = attrs.get("reason_explains_assertion", False)

            if explains and (not a_true or not r_true):
                raise serializers.ValidationError(
                    {
                        "reason_explains_assertion": [
                            "Reason cannot explain assertion if either assertion or reason is false."
                        ]
                    }
                )

            if a_true and r_true:
                derived_relationship = (
                    AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT
                    if explains
                    else AssertionReasonRelationship.BOTH_TRUE_REASON_NOT_CORRECT
                )
            elif a_true and not r_true:
                derived_relationship = AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE
            elif not a_true and not r_true:
                derived_relationship = AssertionReasonRelationship.ASSERTION_FALSE_REASON_FALSE
            else:
                raise serializers.ValidationError(
                    "Combination 'assertion_true=False, reason_true=True' is not supported by domain relationship categories."
                )

        if has_relationship and has_booleans:
            if attrs["correct_relationship"] != derived_relationship:
                raise serializers.ValidationError(
                    f"Provided correct_relationship '{attrs['correct_relationship']}' contradicts boolean flags (derived '{derived_relationship}')."
                )

        final_relationship = attrs.get("correct_relationship") or derived_relationship

        return {
            "assertion": assertion,
            "reason": reason,
            "correct_relationship": final_relationship,
        }


class MatchItemRequestSerializer(serializers.Serializer):
    text = serializers.CharField(
        required=True,
        min_length=1,
        help_text="Match item display text.",
    )
    position = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="1-based position for referencing in pairs.",
    )


class MatchPairRequestSerializer(serializers.Serializer):
    left_position = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Position of the matched item on the LEFT side.",
    )
    right_position = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Position of the matched item on the RIGHT side.",
    )


class MatchFollowingContentRequestSerializer(serializers.Serializer):
    left_items = serializers.ListField(
        child=MatchItemRequestSerializer(),
        min_length=2,
        help_text="List of items appearing on the LEFT column (minimum 2).",
    )
    right_items = serializers.ListField(
        child=MatchItemRequestSerializer(),
        min_length=2,
        help_text="List of items appearing on the RIGHT column (minimum 2).",
    )
    pairs = serializers.ListField(
        child=MatchPairRequestSerializer(),
        min_length=2,
        help_text="Matching pairs mapping each LEFT item position to a RIGHT item position.",
    )


class DescriptiveContentRequestSerializer(serializers.Serializer):
    marks = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Strictly positive maximum marks allocated for this question.",
    )
    expected_answer = serializers.CharField(
        required=True,
        min_length=1,
        help_text="Expected reference answer or evaluation rubric.",
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            allowed = {"marks", "expected_answer"}
            unknown = set(data.keys()) - allowed
            if unknown:
                raise serializers.ValidationError(
                    f"Unsupported fields in descriptive content: {sorted(list(unknown))}. "
                    "Only 'marks' and 'expected_answer' are supported by the domain model."
                )
        return super().to_internal_value(data)
