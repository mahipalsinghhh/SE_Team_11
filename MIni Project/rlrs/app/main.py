"""Application factory. Run with:  uvicorn app.main:create_app --factory --reload"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.config import Settings
from app.db import make_engine, make_session_factory
from app.models import Base
from app.worker.mailer import mailer_from_settings
from app.worker.runner import start_scheduler

UI_DIR = Path(__file__).parent / "ui"


def create_app(settings: Settings | None = None, mailer=None, start_worker: bool | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = make_engine(settings.database_url)
    Base.metadata.create_all(engine)

    mailer = mailer or mailer_from_settings(settings)
    run_worker = settings.worker_enabled if start_worker is None else start_worker

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        sched = start_scheduler(app.state.session_factory, mailer, settings) if run_worker else None
        yield
        if sched:
            sched.shutdown(wait=False)
        engine.dispose()

    app = FastAPI(title="Remote Lab Reservation System", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    app.state.mailer = mailer
    app.include_router(api_router)
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/ui/")

    return app
