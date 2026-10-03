from sqlalchemy import inspect, text

from cloud_native_ai_backend.database import engine


def test_runtime_database_has_migrated_core_tables() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert {"organizations", "users", "memberships", "jobs", "audit_events"} <= tables


def test_runtime_database_accepts_transactional_query() -> None:
    with engine.begin() as connection:
        result = connection.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
