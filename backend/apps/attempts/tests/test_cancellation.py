import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest

from apps.attempts.application import cancel_active_attempt, cancel_attempt, cancel_submitted_attempt
from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    InvalidAttemptStateError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptItem,
    AttemptResponse,
    AttemptResult,
    AttemptStatus,
    ScoreFloorPolicy,
)
from apps.attempts.models.enums import AttemptResultStatus


@pytest.mark.django_db
class TestAttemptCancellation:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.fixed_now = datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.cancel_now = datetime(2026, 10, 1, 11, 0, 0, tzinfo=timezone.utc)
        self.student_id = uuid.uuid4()
        self.superadmin_id = uuid.uuid4()
        self.paper_id = uuid.uuid4()

        self.superadmin_auth = AuthorizationContext(
            actor_id=self.superadmin_id,
            is_student=False,
            is_superadmin=True,
        )
        self.student_auth = AuthorizationContext(
            actor_id=self.student_id,
            is_student=True,
            is_superadmin=False,
        )

        # 1. Active attempt
        self.active_attempt = Attempt.objects.create(
            student_id=self.student_id,
            assessment_paper_id=self.paper_id,
            attempt_number=1,
            duration_seconds=3600,
            started_at=self.fixed_now,
            expires_at=self.fixed_now,
            status=AttemptStatus.IN_PROGRESS,
            score_floor_policy=ScoreFloorPolicy.UNRESTRICTED,
        )
        self.item1 = AttemptItem.objects.create(
            attempt=self.active_attempt,
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            presentation_order=1,
            allocated_marks=Decimal("2.0000"),
            allocated_penalty=Decimal("0.5000"),
        )
        self.resp1 = AttemptResponse.objects.create(
            attempt_item=self.item1,
            answer_state=AnswerState.ANSWERED,
            boolean_response=True,
        )

        # 2. Submitted pending attempt
        self.submitted_attempt = Attempt.objects.create(
            student_id=self.student_id,
            assessment_paper_id=uuid.uuid4(),
            attempt_number=1,
            duration_seconds=3600,
            started_at=self.fixed_now,
            expires_at=self.fixed_now,
            submitted_at=self.fixed_now,
            submission_reason="MANUAL",
            status=AttemptStatus.SUBMITTED,
            score_floor_policy=ScoreFloorPolicy.UNRESTRICTED,
        )
        self.pending_result = AttemptResult.objects.create(
            attempt=self.submitted_attempt,
            status=AttemptResultStatus.PENDING,
            raw_score=Decimal("0.0000"),
            score=Decimal("0.00"),
            maximum_score=Decimal("10.00"),
            percentage=Decimal("0.00"),
            total_questions=1,
            attempted_questions=0,
            correct_questions=0,
            incorrect_questions=0,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=1,
            finalized_at=None,
        )

        # 3. Evaluated / Final attempt
        self.evaluated_attempt = Attempt.objects.create(
            student_id=self.student_id,
            assessment_paper_id=uuid.uuid4(),
            attempt_number=1,
            duration_seconds=3600,
            started_at=self.fixed_now,
            expires_at=self.fixed_now,
            submitted_at=self.fixed_now,
            submission_reason="MANUAL",
            status=AttemptStatus.EVALUATED,
            score_floor_policy=ScoreFloorPolicy.UNRESTRICTED,
        )
        self.final_result = AttemptResult.objects.create(
            attempt=self.evaluated_attempt,
            status=AttemptResultStatus.FINAL,
            raw_score=Decimal("10.0000"),
            score=Decimal("10.00"),
            maximum_score=Decimal("10.00"),
            percentage=Decimal("100.00"),
            total_questions=1,
            attempted_questions=1,
            correct_questions=1,
            incorrect_questions=0,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=0,
            finalized_at=self.fixed_now,
        )

    def test_only_authorized_superadmin_can_cancel(self):
        with pytest.raises(AttemptAuthorizationError):
            cancel_attempt(
                attempt_id=self.active_attempt.id,
                reason="Administrative invalidation",
                authorization=self.student_auth,
            )

    def test_cancel_active_attempt_workflow(self):
        attempt, result = cancel_attempt(
            attempt_id=self.active_attempt.id,
            reason="Technical issue during testing",
            authorization=self.superadmin_auth,
            now=self.cancel_now,
        )

        assert attempt.status == AttemptStatus.CANCELLED
        assert attempt.cancelled_at == self.cancel_now
        assert attempt.cancelled_by == self.superadmin_id
        assert attempt.cancellation_reason == "Technical issue during testing"
        assert result is None

        # Verify historical data is preserved
        assert AttemptItem.objects.filter(attempt=attempt).count() == 1
        resp = AttemptResponse.objects.get(attempt_item=self.item1)
        assert resp.answer_state == AnswerState.ANSWERED
        assert resp.boolean_response is True

    def test_cancel_submitted_pending_attempt_workflow(self):
        attempt, result = cancel_attempt(
            attempt_id=self.submitted_attempt.id,
            reason="Suspected irregularity",
            authorization=self.superadmin_auth,
            now=self.cancel_now,
        )

        assert attempt.status == AttemptStatus.CANCELLED
        assert attempt.cancelled_at == self.cancel_now
        assert attempt.cancelled_by == self.superadmin_id
        assert attempt.cancellation_reason == "Suspected irregularity"

        assert result is not None
        assert result.status == AttemptResultStatus.VOID
        assert result.finalized_at is None

    def test_cannot_cancel_evaluated_or_final_attempt(self):
        with pytest.raises(InvalidAttemptStateError) as cm:
            cancel_attempt(
                attempt_id=self.evaluated_attempt.id,
                reason="Cannot cancel completed attempt",
                authorization=self.superadmin_auth,
            )
        assert "Cannot cancel attempt with status 'EVALUATED'" in str(cm.value)

    def test_cannot_cancel_already_cancelled_attempt(self):
        # Cancel first time
        cancel_attempt(
            attempt_id=self.active_attempt.id,
            reason="Initial cancellation",
            authorization=self.superadmin_auth,
        )

        # Cancel second time should fail
        with pytest.raises(InvalidAttemptStateError) as cm:
            cancel_attempt(
                attempt_id=self.active_attempt.id,
                reason="Second cancellation",
                authorization=self.superadmin_auth,
            )
        assert "Cannot cancel attempt with status 'CANCELLED'" in str(cm.value)

    def test_cancellation_reason_cannot_be_empty(self):
        with pytest.raises(InvalidAttemptStateError) as cm1:
            cancel_attempt(
                attempt_id=self.active_attempt.id,
                reason="",
                authorization=self.superadmin_auth,
            )
        assert "non-empty cancellation reason" in str(cm1.value)

        with pytest.raises(InvalidAttemptStateError) as cm2:
            cancel_attempt(
                attempt_id=self.active_attempt.id,
                reason="   ",
                authorization=self.superadmin_auth,
            )
        assert "non-empty cancellation reason" in str(cm2.value)

    def test_convenience_wrappers(self):
        # cancel_active_attempt wrapper
        act = cancel_active_attempt(
            attempt_id=self.active_attempt.id,
            reason="Wrapper test",
            authorization=self.superadmin_auth,
            now=self.cancel_now,
        )
        assert act.status == AttemptStatus.CANCELLED

        # cancel_submitted_attempt wrapper
        sub, res = cancel_submitted_attempt(
            attempt_id=self.submitted_attempt.id,
            reason="Wrapper test submitted",
            authorization=self.superadmin_auth,
            now=self.cancel_now,
        )
        assert sub.status == AttemptStatus.CANCELLED
        assert res.status == AttemptResultStatus.VOID
