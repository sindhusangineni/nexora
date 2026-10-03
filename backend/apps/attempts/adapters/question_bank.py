from uuid import UUID
from django.apps import apps

from apps.attempts.ports.question_bank import (
    ObjectiveAnswerKeyDTO,
    QuestionBankPort,
)


class DatabaseQuestionBankAnswerKeyAdapter(QuestionBankPort):
    """
    Production adapter retrieving objective answer keys directly from Question Bank
    using dynamic model resolution. Avoids static model imports and preserves
    Clean Architecture modular monolith boundaries.
    """

    def get_objective_answer_keys(
        self,
        pinned_version_ids: list[UUID],
    ) -> dict[UUID, ObjectiveAnswerKeyDTO]:
        if not pinned_version_ids:
            return {}

        QuestionVersion = apps.get_model("question_bank", "QuestionVersion")
        QuestionVersionChoice = apps.get_model("question_bank", "QuestionVersionChoice")
        TrueFalseContent = apps.get_model("question_bank", "TrueFalseContent")
        AssertionReasonContent = apps.get_model("question_bank", "AssertionReasonContent")
        MatchFollowingPair = apps.get_model("question_bank", "MatchFollowingPair")

        versions = list(
            QuestionVersion.objects.filter(id__in=pinned_version_ids)
            .values("id", "question_type")
        )
        if not versions:
            return {}

        version_type_map = {v["id"]: v["question_type"] for v in versions}
        mcq_version_ids = [vid for vid, qtype in version_type_map.items() if qtype in ("MCQ", "MULTIPLE_SELECT")]
        tf_version_ids = [vid for vid, qtype in version_type_map.items() if qtype == "TRUE_FALSE"]
        ar_version_ids = [vid for vid, qtype in version_type_map.items() if qtype == "ASSERTION_REASON"]
        mf_version_ids = [vid for vid, qtype in version_type_map.items() if qtype == "MATCH_FOLLOWING"]

        # Fetch correct choices for MCQ and MULTIPLE_SELECT
        correct_choices_map: dict[UUID, set[UUID]] = {vid: set() for vid in mcq_version_ids}
        if mcq_version_ids:
            choices = QuestionVersionChoice.objects.filter(
                question_version_id__in=mcq_version_ids,
                is_correct=True,
            ).values("question_version_id", "id")
            for c in choices:
                correct_choices_map.setdefault(c["question_version_id"], set()).add(c["id"])

        # Fetch correct boolean for TRUE_FALSE
        tf_map: dict[UUID, bool | None] = {}
        if tf_version_ids:
            tf_contents = TrueFalseContent.objects.filter(
                question_version_id__in=tf_version_ids
            ).values("question_version_id", "answer")
            for tf in tf_contents:
                tf_map[tf["question_version_id"]] = tf["answer"]

        # Fetch correct assertion_reason for ASSERTION_REASON
        ar_map: dict[UUID, str | None] = {}
        if ar_version_ids:
            ar_contents = AssertionReasonContent.objects.filter(
                question_version_id__in=ar_version_ids
            ).values("question_version_id", "correct_relationship")
            for ar in ar_contents:
                ar_map[ar["question_version_id"]] = ar["correct_relationship"]

        # Fetch correct match pairs for MATCH_FOLLOWING
        mf_map: dict[UUID, dict[UUID, UUID]] = {vid: {} for vid in mf_version_ids}
        if mf_version_ids:
            pairs = MatchFollowingPair.objects.filter(
                question_version_id__in=mf_version_ids
            ).values("question_version_id", "left_item_id", "right_item_id")
            for p in pairs:
                mf_map.setdefault(p["question_version_id"], {})[p["left_item_id"]] = p["right_item_id"]

        result: dict[UUID, ObjectiveAnswerKeyDTO] = {}
        for vid, qtype in version_type_map.items():
            if qtype in ("MCQ", "MULTIPLE_SELECT"):
                result[vid] = ObjectiveAnswerKeyDTO(
                    question_version_id=vid,
                    question_type=qtype,
                    correct_choice_ids=correct_choices_map.get(vid, set()),
                    correct_boolean=None,
                    correct_assertion_reason=None,
                    correct_match_pairs={},
                )
            elif qtype == "TRUE_FALSE":
                result[vid] = ObjectiveAnswerKeyDTO(
                    question_version_id=vid,
                    question_type=qtype,
                    correct_choice_ids=set(),
                    correct_boolean=tf_map.get(vid),
                    correct_assertion_reason=None,
                    correct_match_pairs={},
                )
            elif qtype == "ASSERTION_REASON":
                result[vid] = ObjectiveAnswerKeyDTO(
                    question_version_id=vid,
                    question_type=qtype,
                    correct_choice_ids=set(),
                    correct_boolean=None,
                    correct_assertion_reason=ar_map.get(vid),
                    correct_match_pairs={},
                )
            elif qtype == "MATCH_FOLLOWING":
                result[vid] = ObjectiveAnswerKeyDTO(
                    question_version_id=vid,
                    question_type=qtype,
                    correct_choice_ids=set(),
                    correct_boolean=None,
                    correct_assertion_reason=None,
                    correct_match_pairs=mf_map.get(vid, {}),
                )
            elif qtype == "DESCRIPTIVE":
                result[vid] = ObjectiveAnswerKeyDTO(
                    question_version_id=vid,
                    question_type="DESCRIPTIVE",
                    correct_choice_ids=set(),
                    correct_boolean=None,
                    correct_assertion_reason=None,
                    correct_match_pairs={},
                )

        return result
