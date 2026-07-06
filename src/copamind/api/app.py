"""Fábrica da aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from copamind import __version__
from copamind.api.routes import (
    chat_router,
    data_router,
    health_router,
    pool_router,
    predictions_router,
    rag_router,
    simulations_router,
    user_reports_router,
)
from copamind.core.config import Settings, get_settings
from copamind.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Cria e configura a instância da aplicação FastAPI.

    Args:
        settings: configuração opcional; se ausente usa :func:`get_settings`.
    """
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json_logs=settings.log_json)

    app = FastAPI(
        title="CopaMind 2026",
        description="Plataforma local e open source de inteligência esportiva.",
        version=__version__,
    )

    app.include_router(health_router)
    app.include_router(data_router)
    app.include_router(predictions_router)
    app.include_router(simulations_router)
    app.include_router(pool_router)
    app.include_router(user_reports_router)
    app.include_router(rag_router)
    app.include_router(chat_router)

    return app


app = create_app()
