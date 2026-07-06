"""Fábrica da aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from copamind import __version__
from copamind.api.routes import data_router, health_router, predictions_router
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

    return app


app = create_app()
