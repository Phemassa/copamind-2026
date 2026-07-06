"""Núcleo transversal: configuração e logging."""

from copamind.core.config import Settings, get_settings
from copamind.core.logging import configure_logging, get_logger

__all__ = ["Settings", "configure_logging", "get_logger", "get_settings"]
