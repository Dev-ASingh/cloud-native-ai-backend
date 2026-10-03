from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


database_url = get_settings().database_url
engine_kwargs: dict[str, object] = {"future": True, "pool_pre_ping": True}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def initialize_database() -> None:
    from .models import (  # noqa: F401
        IdempotencyRecord,
        JobRecord,
        MembershipRecord,
        OrganizationRecord,
        SessionRecord,
        UserRecord,
    )

    Base.metadata.create_all(bind=engine)
