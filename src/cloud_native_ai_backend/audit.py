from uuid import UUID

from sqlalchemy.orm import Session

from .models import AuditEventRecord


class AuditWriter:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        *,
        organization_id: str,
        actor_id: str,
        action: str,
        target_id: UUID | str,
        outcome: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.session.add(
            AuditEventRecord(
                organization_id=organization_id,
                actor_id=actor_id,
                action=action,
                target_id=str(target_id),
                outcome=outcome,
                event_metadata=metadata or {},
            )
        )
