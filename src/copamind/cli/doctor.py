"""Diagnóstico do ambiente para o comando ``copamind doctor`` (MASTER_PLAN §24).

Verifica Python, dependências, diretórios, arquivos de configuração, espaço em
disco e conectividade opcional com Qdrant, LM Studio e Ollama. Serviços externos
indisponíveis geram aviso (WARN), não falha — a fundação deve rodar offline.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import httpx

from copamind.core.config import Settings, get_settings

# Espaço mínimo em disco recomendado, em GB.
MIN_FREE_DISK_GB = 5.0

# Versão mínima de Python exigida pelo projeto.
MIN_PYTHON = (3, 12)

# Dependências centrais que devem estar importáveis.
CORE_DEPENDENCIES = ("fastapi", "uvicorn", "typer", "pydantic", "structlog", "httpx", "yaml")


class CheckStatus(StrEnum):
    """Resultado de uma verificação individual."""

    ok = "OK"
    warn = "WARN"
    fail = "FAIL"


@dataclass(frozen=True)
class CheckResult:
    """Resultado de uma verificação do ``doctor``."""

    name: str
    status: CheckStatus
    detail: str


def _check_python() -> CheckResult:
    current = sys.version_info[:2]
    if current >= MIN_PYTHON:
        return CheckResult("Python", CheckStatus.ok, f"{current[0]}.{current[1]}")
    return CheckResult(
        "Python",
        CheckStatus.fail,
        f"requer >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}, encontrado {current[0]}.{current[1]}",
    )


def _check_dependencies() -> CheckResult:
    missing = [dep for dep in CORE_DEPENDENCIES if importlib.util.find_spec(dep) is None]
    if not missing:
        return CheckResult("Dependências", CheckStatus.ok, "todas presentes")
    return CheckResult("Dependências", CheckStatus.fail, f"ausentes: {', '.join(missing)}")


def _check_optional_dependency(name: str, import_name: str) -> CheckResult:
    if importlib.util.find_spec(import_name) is not None:
        return CheckResult(name, CheckStatus.ok, "instalado")
    return CheckResult(name, CheckStatus.warn, "não instalado (extra 'data')")


def _check_directories() -> CheckResult:
    required = [
        Path("data"),
        Path("config"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    if not missing:
        return CheckResult("Diretórios", CheckStatus.ok, "presentes")
    return CheckResult("Diretórios", CheckStatus.warn, f"ausentes: {', '.join(missing)}")


def _check_config_files() -> CheckResult:
    example = Path(".env.example")
    if not example.exists():
        return CheckResult("Configuração", CheckStatus.warn, ".env.example ausente")
    if Path(".env").exists():
        return CheckResult("Configuração", CheckStatus.ok, ".env presente")
    return CheckResult("Configuração", CheckStatus.warn, ".env ausente (copie de .env.example)")


def _check_disk() -> CheckResult:
    free_gb = shutil.disk_usage(Path.cwd()).free / (1024**3)
    if free_gb >= MIN_FREE_DISK_GB:
        return CheckResult("Disco", CheckStatus.ok, f"{free_gb:.1f} GB livres")
    return CheckResult(
        "Disco",
        CheckStatus.warn,
        f"{free_gb:.1f} GB livres (recomendado >= {MIN_FREE_DISK_GB:.0f} GB)",
    )


def _check_vram(settings: Settings) -> CheckResult:
    from copamind.llm.hardware import detect_vram_gb, suggest_profile

    vram = detect_vram_gb()
    suggested = suggest_profile(vram)
    active = settings.hardware_profile.value
    if vram is None:
        return CheckResult(
            "GPU/VRAM",
            CheckStatus.warn,
            f"não detectada (perfil ativo: {active}, sugerido: {suggested})",
        )
    detail = f"{vram:.0f} GB — perfil ativo: {active}, sugerido: {suggested}"
    status = CheckStatus.ok if active == suggested else CheckStatus.warn
    return CheckResult("GPU/VRAM", status, detail)


def _probe_http(name: str, url: str, *, timeout: float = 2.0) -> CheckResult:
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return CheckResult(name, CheckStatus.warn, f"indisponível ({type(exc).__name__})")
    return CheckResult(name, CheckStatus.ok, "acessível")


def _check_qdrant(settings: Settings) -> CheckResult:
    return _probe_http("Qdrant", f"{settings.qdrant_url}/healthz")


def _check_lmstudio(settings: Settings) -> CheckResult:
    return _probe_http("LM Studio", f"{settings.lmstudio_base_url}/models")


def _check_ollama(settings: Settings) -> CheckResult:
    return _probe_http("Ollama", f"{settings.ollama_base_url}/api/tags")


def run_diagnostics(settings: Settings | None = None) -> list[CheckResult]:
    """Executa todas as verificações e retorna os resultados.

    Args:
        settings: configuração opcional; se ausente usa :func:`get_settings`.
    """
    settings = settings or get_settings()
    return [
        _check_python(),
        _check_dependencies(),
        _check_optional_dependency("DuckDB", "duckdb"),
        _check_optional_dependency("Polars", "polars"),
        _check_directories(),
        _check_config_files(),
        _check_disk(),
        _check_vram(settings),
        _check_qdrant(settings),
        _check_lmstudio(settings),
        _check_ollama(settings),
    ]


def has_failures(results: list[CheckResult]) -> bool:
    """Indica se algum resultado tem status ``FAIL``."""
    return any(r.status is CheckStatus.fail for r in results)
