import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import SessionRecord


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(
    session: Session,
    user_id: str,
    organization_id: str,
    lifetime: timedelta,
) -> str:
    if lifetime <= timedelta(0):
        raise ValueError("Session lifetime must be positive.")
    token = secrets.token_urlsafe(32)
    session.add(
        SessionRecord(
            id=uuid4().hex,
            token_hash=hash_session_token(token),
            user_id=user_id,
            organization_id=organization_id,
            expires_at=datetime.now(UTC) + lifetime,
            revoked=False,
        )
    )
    session.commit()
    return token


def revoke_session(session: Session, token: str) -> bool:
    record = session.scalar(
        select(SessionRecord).where(SessionRecord.token_hash == hash_session_token(token))
    )
    if record is None or record.revoked:
        return False
    record.revoked = True
    session.commit()
    return True
