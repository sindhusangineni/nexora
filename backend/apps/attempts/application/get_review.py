from uuid import UUID

from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptNotFoundError,
    InvalidAttemptStateError,
)
from apps.attempts.models import Attempt, AttemptStatus
from apps.attempts.models.enums import AttemptResultStatus, EvaluationState
from apps.attempts.ports.question_bank import QuestionBankPort


def get_attempt_review(
    *,
    attempt_id: UUID,
    authorization: AuthorizationContext,
    question_bank_port: QuestionBankPort | None = None,
) -> dict:
    """
    Use Case: Retrieve question-by-question review of an attempt.

    Enforces:
    - Authenticated student can only access their own attempt.
    - Superadmin can access any attempt.
    - Rejects IN_PROGRESS attempts with InvalidAttemptStateError.
    - Immutable snapshot: pinned QuestionVersion via QuestionBankPort.
    - Security Boundary:
      - FINAL: Student receives correct answers, explanations, and awarded marks.
      - PENDING / VOID: Student receives candidate answers and evaluation state;
        correct answers and explanations are withheld (None).
      - Superadmin: Always receives complete solution and audit metadata.
    """
    attempt = (
        Attempt.objects.filter(id=attempt_id)
        .select_related("result")
        .prefetch_related(
            "items__choices",
            "items__response__choices",
            "items__response__matches",
            "items__evaluation",
            "result__section_results",
        )
        .first()
    )
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

    if not authorization.is_superadmin:
        if attempt.student_id != authorization.actor_id:
            raise AttemptAuthorizationError("Students may only view their own test attempts.")
        if attempt.status == AttemptStatus.IN_PROGRESS:
            raise AttemptAuthorizationError("Students cannot review an attempt that is still in progress.")

    has_result = hasattr(attempt, "result") and attempt.result is not None
    result_status = attempt.result.status if has_result else AttemptResultStatus.PENDING

    # Solution visibility rule
    if authorization.is_superadmin:
        show_solution = True
    else:
        show_solution = bool(has_result and result_status == AttemptResultStatus.FINAL)

    # Section title mapping from historical AttemptSectionResult
    section_title_map: dict[UUID, str] = {}
    if has_result:
        for sr in attempt.result.section_results.all():
            section_title_map[sr.assessment_section_id] = sr.section_title_snapshot

    # Fallback to AssessmentSection for any unmapped sections
    unmapped_section_ids = {
        item.assessment_section_id
        for item in attempt.items.all()
        if item.assessment_section_id and item.assessment_section_id not in section_title_map
    }
    if unmapped_section_ids:
        try:
            from django.apps import apps
            AssessmentSection = apps.get_model("assessment", "AssessmentSection")
            for sec in AssessmentSection.objects.filter(id__in=unmapped_section_ids).values("id", "title"):
                section_title_map[sec["id"]] = sec["title"]
        except LookupError:
            pass

    # Fetch pinned question snapshots
    if question_bank_port is None:
        from apps.attempts.adapters.question_bank import DatabaseQuestionBankAnswerKeyAdapter
        question_bank_port = DatabaseQuestionBankAnswerKeyAdapter()

    items = list(attempt.items.all().order_by("presentation_order"))
    pinned_version_ids = [item.question_version_id for item in items]
    snapshots = question_bank_port.get_question_review_snapshots(pinned_version_ids)

    review_items = []
    for item in items:
        snapshot = snapshots.get(item.question_version_id)
        q_type = snapshot.question_type if snapshot else "MCQ"
        q_text = snapshot.text if snapshot else ""
        explanation = (snapshot.explanation if snapshot else "") if show_solution else None
        taxonomy = snapshot.taxonomy if snapshot else None

        resp = getattr(item, "response", None)
        answer_state = resp.answer_state if resp else "UNANSWERED"
        is_answered = bool(resp and resp.answer_state == "ANSWERED")

        ev = getattr(item, "evaluation", None)
        if ev is not None:
            evaluation_status = ev.evaluation_state
            if ev.evaluation_state == EvaluationState.PENDING_EVALUATION:
                marks_awarded = None
                marks_deducted = None
                net_marks = None
            else:
                marks_awarded = str(ev.marks_awarded) if ev.marks_awarded is not None else None
                marks_deducted = str(ev.marks_deducted) if ev.marks_deducted is not None else None
                net_marks = str(ev.net_marks) if ev.net_marks is not None else None
        else:
            if not is_answered:
                evaluation_status = EvaluationState.UNATTEMPTED
                marks_awarded = "0.00"
            else:
                evaluation_status = EvaluationState.PENDING_EVALUATION
                marks_awarded = None
            marks_deducted = "0.00"
            net_marks = marks_awarded

        item_data = {
            "id": item.id,
            "paper_item_id": item.paper_item_id,
            "assessment_section_id": item.assessment_section_id,
            "section_name": section_title_map.get(item.assessment_section_id, ""),
            "question_id": item.question_id,
            "question_version_id": item.question_version_id,
            "question_number": item.presentation_order,
            "presentation_order": item.presentation_order,
            "question_type": q_type,
            "question_text": q_text,
            "taxonomy": taxonomy,
            "allocated_marks": str(item.allocated_marks),
            "allocated_penalty": str(item.allocated_penalty),
            "is_answered": is_answered,
            "answer_state": answer_state,
            "evaluation_status": evaluation_status,
            "marks_awarded": marks_awarded,
            "explanation": explanation,
        }

        # Type-specific representations
        if q_type in ("MCQ", "MULTIPLE_SELECT"):
            raw_choices = snapshot.choices if snapshot else []
            choice_text_map = {c["id"]: c["text"] for c in raw_choices}
            choice_correct_map = {c["id"]: c["is_correct"] for c in raw_choices}

            # Map presented choices in order of AttemptItemChoice.presented_position
            presented_choices = []
            for ic in item.choices.all().order_by("presented_position"):
                cid_str = str(ic.choice_id)
                ch_dict = {
                    "id": cid_str,
                    "text": choice_text_map.get(cid_str, ""),
                    "position": ic.presented_position,
                }
                if show_solution:
                    ch_dict["is_correct"] = choice_correct_map.get(cid_str, False)
                presented_choices.append(ch_dict)

            # If no AttemptItemChoice exists, fallback to snapshot choices
            if not presented_choices and raw_choices:
                for c in raw_choices:
                    ch_dict = {
                        "id": c["id"],
                        "text": c["text"],
                        "position": c["position"],
                    }
                    if show_solution:
                        ch_dict["is_correct"] = c["is_correct"]
                    presented_choices.append(ch_dict)

            item_data["choices"] = presented_choices

            selected_ids = [str(rc.choice_id) for rc in resp.choices.all()] if resp else []
            if q_type == "MCQ":
                selected_id = selected_ids[0] if selected_ids else None
                item_data["candidate_answer"] = {
                    "selected_choice_id": selected_id,
                    "selected_choice_ids": selected_ids,
                    "selected_choice_text": choice_text_map.get(selected_id) if selected_id else None,
                }
                if show_solution:
                    correct_choice = next((c for c in raw_choices if c.get("is_correct")), None)
                    item_data["correct_answer"] = {
                        "correct_choice_id": correct_choice["id"] if correct_choice else None,
                        "correct_choice_ids": [correct_choice["id"]] if correct_choice else [],
                        "correct_choice_text": correct_choice["text"] if correct_choice else None,
                    }
                else:
                    item_data["correct_answer"] = None
            else:
                item_data["candidate_answer"] = {
                    "selected_choice_ids": selected_ids,
                    "selected_choices": [{"id": cid, "text": choice_text_map.get(cid, "")} for cid in selected_ids],
                }
                if show_solution:
                    correct_choices = [c for c in raw_choices if c.get("is_correct")]
                    item_data["correct_answer"] = {
                        "correct_choice_ids": [c["id"] for c in correct_choices],
                        "correct_choices": [{"id": c["id"], "text": c["text"]} for c in correct_choices],
                    }
                else:
                    item_data["correct_answer"] = None

        elif q_type == "TRUE_FALSE":
            bool_resp = resp.boolean_response if resp else None
            item_data["candidate_answer"] = {"boolean_response": bool_resp}
            if show_solution:
                item_data["correct_answer"] = {
                    "correct_boolean": snapshot.true_false_answer if snapshot else None
                }
            else:
                item_data["correct_answer"] = None

        elif q_type == "ASSERTION_REASON":
            ar_data = snapshot.assertion_reason if snapshot else {}
            item_data["assertion"] = ar_data.get("assertion", "") if ar_data else ""
            item_data["reason"] = ar_data.get("reason", "") if ar_data else ""
            ar_resp = resp.assertion_reason_response if resp else None
            item_data["candidate_answer"] = {"assertion_reason_response": ar_resp}
            if show_solution:
                item_data["correct_answer"] = {
                    "correct_relationship": ar_data.get("correct_relationship") if ar_data else None
                }
            else:
                item_data["correct_answer"] = None

        elif q_type == "MATCH_FOLLOWING":
            mf_data = snapshot.match_following if snapshot else {}
            left_items = mf_data.get("left_items", []) if mf_data else []
            right_items = mf_data.get("right_items", []) if mf_data else []
            left_text_map = {item["id"]: item["text"] for item in left_items}
            right_text_map = {item["id"]: item["text"] for item in right_items}

            item_data["left_items"] = left_items
            item_data["right_items"] = right_items

            matches = []
            if resp:
                for m in resp.matches.all():
                    lid = str(m.left_item_id)
                    rid = str(m.right_item_id)
                    matches.append({
                        "left_item_id": lid,
                        "right_item_id": rid,
                        "left_text": left_text_map.get(lid, ""),
                        "right_text": right_text_map.get(rid, ""),
                    })
            item_data["candidate_answer"] = {"matches": matches}

            if show_solution:
                correct_pairs = []
                for p in (mf_data.get("correct_pairs", []) if mf_data else []):
                    lid = p["left_item_id"]
                    rid = p["right_item_id"]
                    correct_pairs.append({
                        "left_item_id": lid,
                        "right_item_id": rid,
                        "left_text": left_text_map.get(lid, ""),
                        "right_text": right_text_map.get(rid, ""),
                    })
                item_data["correct_answer"] = {"correct_matches": correct_pairs}
            else:
                item_data["correct_answer"] = None

        elif q_type == "DESCRIPTIVE":
            text_resp = resp.text_response if resp else None
            item_data["candidate_answer"] = {"text_response": text_resp}
            if show_solution:
                desc_data = snapshot.descriptive if snapshot else {}
                item_data["correct_answer"] = {
                    "model_answer": desc_data.get("expected_answer", "") if desc_data else ""
                }
            else:
                item_data["correct_answer"] = None

        # Superadmin audit extensions
        if authorization.is_superadmin:
            item_data["is_evaluable"] = bool(
                q_type == "DESCRIPTIVE"
                and evaluation_status == EvaluationState.PENDING_EVALUATION
                and attempt.status == AttemptStatus.SUBMITTED
            )
            item_data["response"] = resp
            item_data["evaluation"] = ev

        review_items.append(item_data)

    result_data = attempt.result if has_result else None

    base_review = {
        "id": attempt.id,
        "student_id": attempt.student_id,
        "assessment_paper_id": attempt.assessment_paper_id,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "result_status": result_status,
        "submission_reason": attempt.submission_reason,
        "duration_seconds": attempt.duration_seconds,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
        "items": review_items,
        "result": result_data,
    }

    if authorization.is_superadmin:
        base_review["expires_at"] = attempt.expires_at
        base_review["cancelled_at"] = attempt.cancelled_at
        base_review["cancelled_by"] = attempt.cancelled_by
        base_review["cancellation_reason"] = attempt.cancellation_reason

    return base_review
