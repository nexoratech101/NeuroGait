from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import AuditLog, User

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("")
def list_audit_log(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    entries = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "log_id": str(e.log_id),
            "user_id": str(e.user_id) if e.user_id else None,
            "action": e.action,
            "target_table": e.target_table,
            "target_id": e.target_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "ip_address": e.ip_address,
        }
        for e in entries
    ]
