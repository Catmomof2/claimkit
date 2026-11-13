"""Audit-log read endpoint — recent entries, most recent first."""
from fastapi import APIRouter, Depends

from models.roles import CAN_READ
from services import audit_log
from services.auth import require_roles

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("")
def list_audit(limit: int = 50, role=Depends(require_roles(*CAN_READ))):
    return audit_log.list_recent(limit=limit)
