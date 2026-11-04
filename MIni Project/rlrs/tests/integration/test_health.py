"""RLRS-1: the app starts against a fresh SQLite database and reports healthy."""
from sqlalchemy import inspect


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_tables_created_on_startup(app):
    tables = set(inspect(app.state.engine).get_table_names())
    assert {"users", "labs", "equipment", "reservations", "maintenance_blocks",
            "reminder_jobs", "outbox_emails", "audit_events"} <= tables


def test_ui_served(client):
    r = client.get("/ui/")
    assert r.status_code == 200
    assert "Remote Lab Reservation System" in r.text
