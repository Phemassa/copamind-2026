"""Perfis de hardware para LLMs locais (E10, MASTER_PLAN §37.4, DECISIONS ADR-0003).

Permite escalar de 8 GB para 24 GB de VRAM apenas trocando o perfil de
configuração — sem refatorar o código. Detecta a VRAM disponível e sugere o
perfil adequado. A execução sequencial é sempre o default reprodutível;
concorrência é opt-in do perfil 24 GB.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

DEFAULT_MODELS_PATH = Path("config/models.yaml")
EXAMPLE_MODELS_PATH = Path("config/models.example.yaml")

# Limiar (GB) para sugerir o perfil de 24 GB.
VRAM_24GB_THRESHOLD = 20.0


class HardwareProfile(BaseModel):
    """Parâmetros de execução de um perfil de hardware."""

    name: str
    max_concurrent_models: int = Field(default=1, ge=1)
    default_quantization: str = "Q4_K_M"
    default_context_length: int = Field(default=8192, ge=512)
    execution: str = "sequential"

    @property
    def allows_concurrency(self) -> bool:
        """Indica se o perfil permite execução concorrente (opt-in)."""
        return self.max_concurrent_models > 1 and self.execution == "concurrent"


def load_hardware_profiles(path: str | Path | None = None) -> dict[str, HardwareProfile]:
    """Carrega os perfis de hardware de `models.yaml` (ou do exemplo)."""
    resolved = Path(path) if path is not None else DEFAULT_MODELS_PATH
    if not resolved.exists():
        resolved = EXAMPLE_MODELS_PATH
    if not resolved.exists():
        raise FileNotFoundError("nenhum arquivo de modelos encontrado")

    data: dict[str, Any] = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    profiles: dict[str, HardwareProfile] = {}
    for name, entry in (data.get("hardware_profiles") or {}).items():
        profiles[name] = HardwareProfile(
            name=name,
            max_concurrent_models=int(entry.get("max_concurrent_models", 1)),
            default_quantization=str(entry.get("default_quantization", "Q4_K_M")),
            default_context_length=int(entry.get("default_context_length", 8192)),
            execution=str(entry.get("execution", "sequential")),
        )
    return profiles


def get_hardware_profile(name: str, path: str | Path | None = None) -> HardwareProfile | None:
    """Retorna um perfil pelo nome (ex.: '8gb', '24gb')."""
    return load_hardware_profiles(path).get(name)


def detect_vram_gb() -> float | None:
    """Detecta a VRAM total da primeira GPU NVIDIA via `nvidia-smi` (ou None)."""
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        output = subprocess.run(  # nosec B603 B607
            [
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    first = output.strip().splitlines()
    if not first:
        return None
    try:
        return float(first[0].strip()) / 1024.0
    except ValueError:
        return None


def suggest_profile(vram_gb: float | None) -> str:
    """Sugere o nome do perfil a partir da VRAM detectada."""
    if vram_gb is not None and vram_gb >= VRAM_24GB_THRESHOLD:
        return "24gb"
    return "8gb"
