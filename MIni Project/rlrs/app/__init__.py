"""RLRS web application (FastAPI + SQLAlchemy/SQLite).

Layers (see docs/diagrams/05_component.puml):
    app/api      REST endpoints
    app/engine   services that wire rlrs_core (the scheduling engine logic) to the database
    app/models   SQLAlchemy ORM models (data layer)
    app/worker   background reminder/notification worker and mailers
    app/ui       static browser UI
"""
