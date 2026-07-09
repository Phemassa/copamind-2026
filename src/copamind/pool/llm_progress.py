"""Persistencia leve de progresso dos batches LLM."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROGRESS_DIR = Path("data/cache/llm_progress")


def read_llm_phase_progress(batch_id: str) -> dict[str, Any] | None:
    """Le o progresso de um batch, quando existir."""
    path = _progress_path(batch_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def read_latest_llm_phase_progress(phase: str | None = None) -> dict[str, Any] | None:
    """Le o progresso mais recente, opcionalmente filtrado por fase."""
    if not PROGRESS_DIR.exists():
        return None
    paths = sorted(PROGRESS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in paths:
        try:
            progress = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if phase and progress.get("phase") != phase:
            continue
        return progress
    return None


def write_llm_phase_progress(batch_id: str, **fields: Any) -> dict[str, Any]:
    """Atualiza o progresso de um batch em arquivo atomico."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    current = read_llm_phase_progress(batch_id) or {"batch_id": batch_id}
    current.update(fields)
    current["batch_id"] = batch_id
    current["updated_at"] = datetime.now(UTC).isoformat()
    path = _progress_path(batch_id)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)
    return current


def new_llm_batch_id() -> str:
    """Novo identificador curto de batch."""
    from uuid import uuid4

    return f"llmbatch-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"


def _progress_path(batch_id: str) -> Path:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in batch_id)
    return PROGRESS_DIR / f"{safe}.json"
