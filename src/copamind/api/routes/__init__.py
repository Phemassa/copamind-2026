"""Rotas da API."""

from copamind.api.routes.data import router as data_router
from copamind.api.routes.health import router as health_router

__all__ = ["data_router", "health_router"]
