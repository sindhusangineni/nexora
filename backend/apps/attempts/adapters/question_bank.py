from uuid import UUID
from django.apps import apps

from apps.attempts.ports.question_bank import (
    ObjectiveAnswerKeyDTO,
    QuestionBankPort,
    QuestionReviewSnapshotDTO,
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

    def get_question_review_snapshots(
        self,
        pinned_version_ids: list[UUID],
    ) -> dict[UUID, QuestionReviewSnapshotDTO]:
        if not pinned_version_ids:
            return {}

        QuestionVersion = apps.get_model("question_bank", "QuestionVersion")
        QuestionTopic = apps.get_model("question_bank", "QuestionTopic")
        QuestionVersionChoice = apps.get_model("question_bank", "QuestionVersionChoice")
        TrueFalseContent = apps.get_model("question_bank", "TrueFalseContent")
        AssertionReasonContent = apps.get_model("question_bank", "AssertionReasonContent")
        MatchFollowingItem = apps.get_model("question_bank", "MatchFollowingItem")
        MatchFollowingPair = apps.get_model("question_bank", "MatchFollowingPair")
        DescriptiveContent = apps.get_model("question_bank", "DescriptiveContent")

        versions = list(
            QuestionVersion.objects.filter(id__in=pinned_version_ids)
            .values("id", "question_id", "question_type", "text", "explanation")
        )
        if not versions:
            return {}

        question_ids = [v["question_id"] for v in versions]

        # Taxonomy mapping: question_id -> {"domain": ..., "subject": ..., "chapter": ..., "topic": ...}
        taxonomy_map: dict[UUID, dict[str, str]] = {}
        qtopics = (
            QuestionTopic.objects.filter(question_id__in=question_ids)
            .select_related("topic__chapter__subject__domain")
        )
        for qt in qtopics:
            topic = qt.topic
            chapter = getattr(topic, "chapter", None)
            subject = getattr(chapter, "subject", None) if chapter else None
            domain = getattr(subject, "domain", None) if subject else None
            taxonomy_map[qt.question_id] = {
                "topic": topic.name if topic else "",
                "chapter": chapter.name if chapter else "",
                "subject": subject.name if subject else "",
                "domain": domain.name if domain else "",
            }

        version_type_map = {v["id"]: v["question_type"] for v in versions}
        mcq_vids = [vid for vid, qtype in version_type_map.items() if qtype in ("MCQ", "MULTIPLE_SELECT")]
        tf_vids = [vid for vid, qtype in version_type_map.items() if qtype == "TRUE_FALSE"]
        ar_vids = [vid for vid, qtype in version_type_map.items() if qtype == "ASSERTION_REASON"]
        mf_vids = [vid for vid, qtype in version_type_map.items() if qtype == "MATCH_FOLLOWING"]
        desc_vids = [vid for vid, qtype in version_type_map.items() if qtype == "DESCRIPTIVE"]

        # Choices for MCQ / MULTIPLE_SELECT
        choices_map: dict[UUID, list[dict]] = {vid: [] for vid in mcq_vids}
        if mcq_vids:
            raw_choices = (
                QuestionVersionChoice.objects.filter(question_version_id__in=mcq_vids)
                .values("id", "question_version_id", "text", "position", "is_correct")
                .order_by("position")
            )
            for c in raw_choices:
                choices_map.setdefault(c["question_version_id"], []).append({
                    "id": str(c["id"]),
                    "text": c["text"],
                    "position": c["position"],
                    "is_correct": c["is_correct"],
                })

        # TRUE_FALSE
        tf_map: dict[UUID, bool | None] = {}
        if tf_vids:
            tfs = TrueFalseContent.objects.filter(
                question_version_id__in=tf_vids
            ).values("question_version_id", "answer")
            for tf in tfs:
                tf_map[tf["question_version_id"]] = tf["answer"]

        # ASSERTION_REASON
        ar_map: dict[UUID, dict] = {}
        if ar_vids:
            ars = AssertionReasonContent.objects.filter(
                question_version_id__in=ar_vids
            ).values("question_version_id", "assertion", "reason", "correct_relationship")
            for ar in ars:
                ar_map[ar["question_version_id"]] = {
                    "assertion": ar["assertion"],
                    "reason": ar["reason"],
                    "correct_relationship": ar["correct_relationship"],
                }

        # MATCH_FOLLOWING
        mf_map: dict[UUID, dict] = {vid: {"left_items": [], "right_items": [], "correct_pairs": []} for vid in mf_vids}
        if mf_vids:
            items = (
                MatchFollowingItem.objects.filter(question_version_id__in=mf_vids)
                .values("id", "question_version_id", "side", "text", "position")
                .order_by("position")
            )
            for item in items:
                side_key = "left_items" if item["side"] == "LEFT" else "right_items"
                mf_map.setdefault(item["question_version_id"], {"left_items": [], "right_items": [], "correct_pairs": []})[side_key].append({
                    "id": str(item["id"]),
                    "text": item["text"],
                    "position": item["position"],
                })

            pairs = (
                MatchFollowingPair.objects.filter(question_version_id__in=mf_vids)
                .values("question_version_id", "left_item_id", "right_item_id")
            )
            for p in pairs:
                mf_map.setdefault(p["question_version_id"], {"left_items": [], "right_items": [], "correct_pairs": []})["correct_pairs"].append({
                    "left_item_id": str(p["left_item_id"]),
                    "right_item_id": str(p["right_item_id"]),
                })

        # DESCRIPTIVE
        desc_map: dict[UUID, dict] = {}
        if desc_vids:
            descs = (
                DescriptiveContent.objects.filter(question_version_id__in=desc_vids)
                .values("question_version_id", "marks", "expected_answer")
            )
            for d in descs:
                desc_map[d["question_version_id"]] = {
                    "marks": d["marks"],
                    "expected_answer": d["expected_answer"],
                }

        snapshots: dict[UUID, QuestionReviewSnapshotDTO] = {}
        for v in versions:
            vid = v["id"]
            snapshots[vid] = QuestionReviewSnapshotDTO(
                question_version_id=vid,
                question_id=v["question_id"],
                question_type=v["question_type"],
                text=v["text"],
                explanation=v["explanation"] or "",
                taxonomy=taxonomy_map.get(v["question_id"]),
                choices=choices_map.get(vid, []),
                true_false_answer=tf_map.get(vid),
                assertion_reason=ar_map.get(vid),
                match_following=mf_map.get(vid),
                descriptive=desc_map.get(vid),
            )

        return snapshots

