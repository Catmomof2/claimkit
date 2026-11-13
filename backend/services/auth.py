"""Role-based access enforcement (starter).

The caller identifies its role with the ``X-ClaimKit-Role`` header
(``admin`` / ``staff`` / ``viewer``; missing or unknown header defaults
to ``viewer`` — the least-privileged role). This is a starter stand-in,
NOT production auth: replace ``get_current_role`` with Supabase JWT
verification before any pilot user touches real data.

Two layers, both used:
- Pure function ``check_role()`` — raises ``PermissionError``; used by
  services and unit tests without FastAPI.
- FastAPI dependency ``require_roles()`` — raises HTTP 403; used by
  API routers.
"""
from fastapi import Header, HTTPException

from models.roles import Role


def parse_role(raw: str | None) -> Role:
    if raw is None:
        return Role.VIEWER
    try:
        return Role(raw.strip().lower())
    except ValueError:
        return Role.VIEWER


def check_role(role: Role, allowed: tuple[Role, ...]) -> None:
    """Raise PermissionError unless ``role`` is in ``allowed``."""
    if role not in allowed:
        raise PermissionError(
            f"Role '{role.value}' may not perform this action. "
            f"Allowed: {', '.join(r.value for r in allowed)}."
        )


def require_roles(*allowed: Role):
    """FastAPI dependency factory: 403 unless the caller's role is allowed."""

    def _require(x_claimkit_role: str | None = Header(default=None)) -> Role:
        role = parse_role(x_claimkit_role)
        if role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Role '{role.value}' may not perform this action. "
                    f"Allowed: {', '.join(r.value for r in allowed)}."
                ),
            )
        return role

    return _require


def get_current_role(x_claimkit_role: str | None = Header(default=None)) -> Role:
    return parse_role(x_claimkit_role)
