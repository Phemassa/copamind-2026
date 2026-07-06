"""Configuração de logging estruturado com structlog (MASTER_PLAN §22).

Suporta saída JSON (produção) ou console colorido (desenvolvimento).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

_configured = False


def configure_logging(*, level: str = "INFO", json_logs: bool = True) -> None:
    """Configura o logging estruturado do processo.

    Idempotente: chamadas repetidas não duplicam handlers.

    Args:
        level: nível de log (ex.: ``"INFO"``, ``"DEBUG"``).
        json_logs: se ``True`` emite JSON; caso contrário, console legível.
    """
    global _configured

    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str | None = None, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado, configurando o logging se necessário.

    Args:
        name: nome do logger (tipicamente ``__name__``).
        **initial_values: pares chave/valor anexados a todas as mensagens.
    """
    if not _configured:
        configure_logging()
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name, **initial_values)
    return logger
