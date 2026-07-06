"""Carregamento de perfis de modelos a partir de `models.yaml` (MASTER_PLAN §15.2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from copamind.llm.orchestrator import ModelSpec

DEFAULT_MODELS_PATH = Path("config/models.yaml")
EXAMPLE_MODELS_PATH = Path("config/models.example.yaml")


def load_model_specs(path: str | Path | None = None) -> dict[str, ModelSpec]:
    """Carrega os specs de analyst/challenger/auditor de um YAML.

    Se ``path`` for omitido, usa `config/models.yaml` e cai para o exemplo.
    """
    resolved = Path(path) if path is not None else DEFAULT_MODELS_PATH
    if not resolved.exists():
        resolved = EXAMPLE_MODELS_PATH
    if not resolved.exists():
        raise FileNotFoundError("nenhum arquivo de modelos encontrado")

    data: dict[str, Any] = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    models = data.get("models", {})
    specs: dict[str, ModelSpec] = {}
    for role in ("analyst", "challenger", "auditor"):
        entry = models.get(role)
        if entry is None:
            continue
        specs[role] = ModelSpec(
            role=entry.get("role", role),
            model_id=entry["model_id"],
            temperature=float(entry.get("temperature", 0.2)),
            unload_after_run=bool(entry.get("unload_after_run", True)),
        )
    return specs
