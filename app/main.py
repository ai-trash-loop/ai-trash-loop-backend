from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import Settings
from app.db import Base, make_engine, make_session_factory
from app.services.engine_client import EngineClient, InProcessEngine


def create_app(settings: Settings | None = None, engine_client: EngineClient | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="AI Trash-Loop API", version="0.1.0")
    db_engine = make_engine(settings.database_url)
    Base.metadata.create_all(db_engine)  # MVP: Alembic once the schema stabilises (docs/adr/0001)
    app.state.settings = settings
    app.state.session_factory = make_session_factory(db_engine)
    app.state.engine_client = engine_client or InProcessEngine()
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET", "POST"], allow_headers=["*"])
    app.include_router(router)
    return app
