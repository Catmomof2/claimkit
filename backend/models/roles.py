"""Role-based access — roles and what they may do.

Roles (see docs/architecture.md and README.md):

- admin  — everything staff can do, plus admin-only actions:
  changing a claim filing deadline and managing the approval queue
  (see api/claims.py PATCH /claims/{id}/deadline).
- staff  — create claims, generate packets, draft / approve / send
  follow-ups (sending still requires a prior approval record),
  upload and extract documents.
- viewer — read-only: list shipments, claims, deadlines, drafts, and
  the audit log. Cannot approve, reject, send, create, or change
  anything. Any write attempt returns 403.

Auth in this starter is a header, ``X-ClaimKit-Role``, read by
services/auth.py. That is deliberately NOT production auth: before
any pilot user touches real data, replace it with Supabase JWT
verification and look the role up from the authenticated user
(see docs/architecture.md).
"""
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"


# Who may do what. Keep this as the single source of truth; the API
# enforces it via services.auth.require_roles().
CAN_CREATE_CLAIM = (Role.ADMIN, Role.STAFF)
CAN_GENERATE_PACKET = (Role.ADMIN, Role.STAFF)
CAN_DRAFT_FOLLOWUP = (Role.ADMIN, Role.STAFF)
CAN_APPROVE_FOLLOWUP = (Role.ADMIN, Role.STAFF)
CAN_REJECT_FOLLOWUP = (Role.ADMIN, Role.STAFF)
CAN_SEND_FOLLOWUP = (Role.ADMIN, Role.STAFF)  # + approval record, always
CAN_CHANGE_DEADLINE = (Role.ADMIN,)  # admin-only
CAN_EXTRACT_DOCUMENT = (Role.ADMIN, Role.STAFF)
CAN_READ = (Role.ADMIN, Role.STAFF, Role.VIEWER)
