"""Rotas da API."""

from copamind.api.routes.admin import router as admin_router
from copamind.api.routes.chat import router as chat_router
from copamind.api.routes.data import router as data_router
from copamind.api.routes.health import router as health_router
from copamind.api.routes.pool import router as pool_router
from copamind.api.routes.predictions import router as predictions_router
from copamind.api.routes.rag import router as rag_router
from copamind.api.routes.simulations import router as simulations_router
from copamind.api.routes.user_reports import router as user_reports_router

__all__ = [
    "admin_router",
    "chat_router",
    "data_router",
    "health_router",
    "pool_router",
    "predictions_router",
    "rag_router",
    "simulations_router",
    "user_reports_router",
]
