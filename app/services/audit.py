import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


class AuditService:

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: uuid.UUID | None,
        action: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: str | None = None
    ) -> AuditLog:
        """Records an immutable audit log entry for security and compliance."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.add(audit_entry)
        await db.commit()
        return audit_entry

    @staticmethod
    async def get_user_logs(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50
    ) -> list[AuditLog]:
        """Retrieves recent audit log history for a user."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
