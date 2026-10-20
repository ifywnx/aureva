"""Guard tests: provisioned Preview accounts can never silently target production."""
from contextlib import contextmanager

import pytest

from scripts.preview_setup import assert_preview_configuration, create_preview_user, inspect_live_preview


@pytest.fixture
def preview(monkeypatch):
    monkeypatch.setenv("AUREVA_DB_SCHEMA", "aureva_preview")
    monkeypatch.delenv("AUREVA_DB", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://aureva_preview_app.epwojwlsibjmxhdbtsqu:private-password@"
        "example.invalid:6543/postgres?sslmode=require",
    )


def test_preview_account_guards_refuse_prod_role_and_schema(monkeypatch, preview):
    assert "aureva_preview_app" in assert_preview_configuration()
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:password@example.invalid/postgres")
    with pytest.raises(RuntimeError, match="Từ chối production"):
        assert_preview_configuration()
    monkeypatch.setenv("DATABASE_URL", "postgresql://aureva_preview_app:password@example.invalid/postgres")
    monkeypatch.setenv("AUREVA_DB_SCHEMA", "aureva")
    with pytest.raises(RuntimeError, match="aureva_preview"):
        assert_preview_configuration()


def test_preview_role_tool_does_not_allow_donor_or_unknown_role(monkeypatch, preview):
    with pytest.raises(ValueError, match="manager hoặc approver"):
        create_preview_user("someone@example.com", "Người thử", "donor")


def test_preview_connection_confirms_role_and_schema(monkeypatch, preview):
    from backend import app as backend

    class Cursor:
        def __init__(self, record):
            self.record = record
        def fetchone(self):
            return self.record

    class FakeConnection:
        def __init__(self, role="aureva_preview_app", schema="aureva_preview", count=11):
            self.role, self.schema, self.count = role, schema, count
        def execute(self, query):
            if "current_user" in query:
                return Cursor({"username": self.role, "active_schema": self.schema})
            if "information_schema.tables" in query:
                return Cursor({"count": self.count})
            if "FROM users" in query:
                return Cursor({"count": 0})
            raise AssertionError("Unexpected SQL query")

    holder = {"connection": FakeConnection()}

    @contextmanager
    def connect():
        yield holder["connection"]

    monkeypatch.setattr(backend, "connect", connect)
    assert inspect_live_preview()
    for connection in (
        FakeConnection(role="postgres"),
        FakeConnection(schema="aureva"),
        FakeConnection(count=10),
    ):
        holder["connection"] = connection
        with pytest.raises(RuntimeError):
            inspect_live_preview()
