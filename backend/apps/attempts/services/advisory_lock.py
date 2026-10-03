import hashlib
import struct
from uuid import UUID

from django.db import connection


def get_attempt_start_lock_key(
    student_id: UUID,
    paper_id: UUID,
) -> int:
    """
    Derive a deterministic signed 64-bit integer key from the MD5 digest
    of the attempt start namespace: attempt_start:<student_id>:<paper_id>.
    """
    namespace = f"attempt_start:{student_id}:{paper_id}".encode("utf-8")
    digest = hashlib.md5(namespace).digest()
    (lock_key,) = struct.unpack(">q", digest[:8])
    return lock_key


def acquire_attempt_start_lock(
    student_id: UUID,
    paper_id: UUID,
) -> None:
    """
    Acquire a PostgreSQL transaction-scoped advisory lock for the attempt start namespace.
    Automatically released upon transaction commit or rollback.

    In non-PostgreSQL environments (such as SQLite in-memory unit tests),
    safely skips PostgreSQL-specific system functions.
    """
    lock_key = get_attempt_start_lock_key(student_id, paper_id)

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                [lock_key],
            )
