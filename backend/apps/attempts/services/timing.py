from datetime import datetime, timezone


def get_authoritative_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def is_attempt_expired(expires_at: datetime, now: datetime) -> bool:
    """
    Authoritative server-side expiry determination.

    Rules:
    - now < expires_at  -> False (attempt is active)
    - now >= expires_at -> True  (attempt is expired)
    """
    return now >= expires_at


def is_attempt_active(expires_at: datetime, now: datetime) -> bool:
    """
    Inverse of is_attempt_expired.

    Rules:
    - now < expires_at  -> True  (attempt is active)
    - now >= expires_at -> False (attempt is expired)
    """
    return now < expires_at
