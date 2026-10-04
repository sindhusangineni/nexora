import hashlib
import struct
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.attempts.authorization import (
    AuthorizationContext,
    validate_can_start_attempt,
)
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptConflictError,
    AttemptError,
    AttemptExpired,
    InvalidAttemptStateError,
    InvalidDeliveryPayloadError,
    PaperNotEligibleError,
)
from apps.attempts.services.advisory_lock import (
    acquire_attempt_start_lock,
    get_attempt_start_lock_key,
)
from apps.attempts.services.timing import (
    get_authoritative_now,
    is_attempt_active,
    is_attempt_expired,
)


class AdvisoryLockServiceTests(TestCase):
    def test_deterministic_same_key_generation(self):
        student_id = uuid.uuid4()
        paper_id = uuid.uuid4()

        key1 = get_attempt_start_lock_key(student_id, paper_id)
        key2 = get_attempt_start_lock_key(student_id, paper_id)
        self.assertEqual(key1, key2)

    def test_different_student_paper_pairs_produce_different_keys(self):
        student_id1 = uuid.uuid4()
        student_id2 = uuid.uuid4()
        paper_id1 = uuid.uuid4()
        paper_id2 = uuid.uuid4()

        key1 = get_attempt_start_lock_key(student_id1, paper_id1)
        key2 = get_attempt_start_lock_key(student_id2, paper_id1)
        key3 = get_attempt_start_lock_key(student_id1, paper_id2)

        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key2, key3)

    def test_key_is_signed_64_bit_integer(self):
        student_id = uuid.uuid4()
        paper_id = uuid.uuid4()
        key = get_attempt_start_lock_key(student_id, paper_id)

        min_signed_64 = -(2**63)
        max_signed_64 = 2**63 - 1
        self.assertTrue(min_signed_64 <= key <= max_signed_64)

    def test_correct_md5_derivation(self):
        student_id = uuid.uuid4()
        paper_id = uuid.uuid4()

        expected_namespace = f"attempt_start:{student_id}:{paper_id}".encode("utf-8")
        expected_digest = hashlib.md5(expected_namespace).digest()
        (expected_key,) = struct.unpack(">q", expected_digest[:8])

        actual_key = get_attempt_start_lock_key(student_id, paper_id)
        self.assertEqual(actual_key, expected_key)

    def test_acquire_attempt_start_lock_executes_cleanly(self):
        student_id = uuid.uuid4()
        paper_id = uuid.uuid4()
        # Executes safely in test environment
        acquire_attempt_start_lock(student_id, paper_id)

    @patch("apps.attempts.services.advisory_lock.connection")
    def test_acquisition_uses_pg_advisory_xact_lock(self, mock_connection):
        mock_connection.vendor = "postgresql"
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        student_id = uuid.uuid4()
        paper_id = uuid.uuid4()
        expected_key = get_attempt_start_lock_key(student_id, paper_id)

        acquire_attempt_start_lock(student_id, paper_id)

        mock_cursor.execute.assert_called_once_with(
            "SELECT pg_advisory_xact_lock(%s)",
            [expected_key],
        )



class TimingServiceTests(TestCase):
    def test_now_before_expires_at_is_active(self):
        now = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)
        expires_at = now + timedelta(minutes=60)

        self.assertTrue(is_attempt_active(expires_at, now))
        self.assertFalse(is_attempt_expired(expires_at, now))

    def test_now_exactly_at_expires_at_is_expired(self):
        now = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)
        expires_at = now

        self.assertFalse(is_attempt_active(expires_at, now))
        self.assertTrue(is_attempt_expired(expires_at, now))

    def test_now_after_expires_at_is_expired(self):
        now = datetime(2026, 10, 3, 12, 0, 1, tzinfo=timezone.utc)
        expires_at = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)

        self.assertFalse(is_attempt_active(expires_at, now))
        self.assertTrue(is_attempt_expired(expires_at, now))

    def test_authoritative_now_returns_utc_datetime(self):
        current = get_authoritative_now()
        self.assertIsNotNone(current.tzinfo)
        self.assertEqual(current.tzinfo, timezone.utc)


class AuthorizationContextTests(TestCase):
    def test_student_starting_own_attempt_is_allowed(self):
        student_id = uuid.uuid4()
        ctx = AuthorizationContext(
            actor_id=student_id,
            is_student=True,
            is_superadmin=False,
        )
        # Should not raise
        validate_can_start_attempt(ctx, student_id)

    def test_student_starting_another_students_attempt_is_rejected(self):
        student_id = uuid.uuid4()
        other_student_id = uuid.uuid4()
        ctx = AuthorizationContext(
            actor_id=student_id,
            is_student=True,
            is_superadmin=False,
        )
        with self.assertRaises(AttemptAuthorizationError) as cm:
            validate_can_start_attempt(ctx, other_student_id)
        self.assertIn("own student_id", str(cm.exception))

    def test_superadmin_without_student_role_rejected(self):
        superadmin_id = uuid.uuid4()
        student_id = uuid.uuid4()
        ctx = AuthorizationContext(
            actor_id=superadmin_id,
            is_student=False,
            is_superadmin=True,
        )
        with self.assertRaises(AttemptAuthorizationError) as cm:
            validate_can_start_attempt(ctx, student_id)
        self.assertIn("Only students are authorized", str(cm.exception))

    def test_non_student_rejected_without_bypass(self):
        actor_id = uuid.uuid4()
        student_id = actor_id
        ctx = AuthorizationContext(
            actor_id=actor_id,
            is_student=False,
            is_superadmin=False,
        )
        with self.assertRaises(AttemptAuthorizationError):
            validate_can_start_attempt(ctx, student_id)


class AttemptExceptionsTests(TestCase):
    def test_attempt_expired_http_status_and_code(self):
        exc = AttemptExpired("Attempt has expired.")
        self.assertEqual(exc.status_code, 409)
        self.assertEqual(exc.code, "ATTEMPT_EXPIRED")
        self.assertEqual(str(exc), "Attempt has expired.")

    def test_other_attempt_exceptions(self):
        auth_exc = AttemptAuthorizationError()
        self.assertEqual(auth_exc.status_code, 403)
        self.assertEqual(auth_exc.code, "AUTHORIZATION_FAILURE")

        paper_exc = PaperNotEligibleError()
        self.assertEqual(paper_exc.status_code, 400)
        self.assertEqual(paper_exc.code, "PAPER_NOT_ELIGIBLE")

        payload_exc = InvalidDeliveryPayloadError()
        self.assertEqual(payload_exc.status_code, 400)
        self.assertEqual(payload_exc.code, "INVALID_DELIVERY_PAYLOAD")

        state_exc = InvalidAttemptStateError()
        self.assertEqual(state_exc.status_code, 400)
        self.assertEqual(state_exc.code, "INVALID_ATTEMPT_STATE")

        conflict_exc = AttemptConflictError()
        self.assertEqual(conflict_exc.status_code, 409)
        self.assertEqual(conflict_exc.code, "ATTEMPT_CONFLICT")
