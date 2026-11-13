"""Supabase Auth design (starter: documented, not enforced).

Production design — implement before any pilot user touches real data:
1. Frontend signs in with Supabase Auth (email / magic link / OAuth).
   Supabase issues a JWT access token.
2. Frontend sends the token as ``Authorization: Bearer <jwt>`` on
   every API call.
3. Backend verifies the JWT against Supabase's JWKS
   (``SUPABASE_URL`` + ``SUPABASE_JWT_SECRET`` / JWKS endpoint),
   extracts the user id, and looks up the user's role from the
   ``users`` table (``database/schemas.sql``).
4. The resolved ``Role`` is then enforced by the existing checks in
   ``services/auth.py`` (``require_roles`` / ``check_role``) and the
   role table in ``models/roles.py``. Nothing else changes.

Starter behaviour: ``verify_supabase_token()`` raises
``NotImplementedError`` — deliberately. The API currently uses the
``X-ClaimKit-Role`` header (see services/auth.py) so the role checks
can be exercised without a Supabase project. Do NOT treat the header
as authentication in production: anyone can send any header.

Environment (never commit real values):
- SUPABASE_URL, SUPABASE_ANON_KEY (frontend)
- SUPABASE_SERVICE_ROLE_KEY (backend only, never in the frontend)
- SUPABASE_JWT_SECRET (or JWKS URL) for token verification
"""
from models.roles import Role


class SupabaseNotConfiguredError(NotImplementedError):
    pass


def verify_supabase_token(token: str) -> tuple[str, Role]:
    """Verify a Supabase JWT and return (user_id, role).

    Starter: not implemented — see module docstring. Implement with
    PyJWT + Supabase JWKS, then look up the role in the users table.
    """
    raise SupabaseNotConfiguredError(
        "Supabase Auth is not configured. Set SUPABASE_URL / "
        "SUPABASE_JWT_SECRET and implement verify_supabase_token() "
        "with JWT verification against Supabase's JWKS."
    )
