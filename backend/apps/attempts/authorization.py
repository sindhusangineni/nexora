from dataclasses import dataclass
from uuid import UUID

from apps.attempts.exceptions import AttemptAuthorizationError


@dataclass(frozen=True)
class AuthorizationContext:
    actor_id: UUID
    is_student: bool
    is_superadmin: bool


def validate_can_start_attempt(
    context: AuthorizationContext,
    student_id: UUID,
) -> None:
    """
    Validate that the actor in the authorization context is allowed to start an attempt.

    Rules:
    - Student may start attempts for themselves (actor_id == student_id).
    - Students cannot start attempts for another student.
    - Actors without the Student role cannot start attempts.
    - is_superuser is NOT treated as an application-role bypass.
    """
    if not context.is_student:
        raise AttemptAuthorizationError("Only students are authorized to start test attempts.")

    if context.actor_id != student_id:
        raise AttemptAuthorizationError("Students may only start attempts for their own student_id.")


def get_authorization_context(user) -> AuthorizationContext:
    """Construct an AuthorizationContext from a Django request user."""
    if not user or not user.is_authenticated:
        return AuthorizationContext(
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            is_student=False,
            is_superadmin=False,
        )
    user_groups = set(user.groups.values_list("name", flat=True))
    return AuthorizationContext(
        actor_id=user.id,
        is_student="Student" in user_groups,
        is_superadmin="Superadmin" in user_groups,
    )

