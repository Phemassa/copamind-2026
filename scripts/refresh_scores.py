"""Atualiza resultados, recalcula scores das LLMs e exporta o portal.

Uso: python scripts/refresh_scores.py [--status-file PATH]

Etapas (sem nenhuma chamada a LLM):
  1. Re-ingere data/samples/worldcup2026_copa.json  → resultados oficiais
  2. run_backtest                                    → pontua os palpites existentes
  3. export_portal_data.py                          → snapshot JSON para o portal
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from copamind.core.config import get_settings
from copamind.data.ingestion.service import ingest_worldcup
from copamind.data.repositories import DuckDBRepository
from copamind.pool.service import run_backtest


def _write_status(path: Path | None, status: str, message: str, step: int, total: int) -> None:
    if not path:
        return
    payload = {
        "status": status,
        "message": message,
        "step": step,
        "total_steps": total,
        "percent": round(step / total * 100) if total else 0,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-file", default="")
    args = parser.parse_args()
    status_path = Path(args.status_file) if args.status_file else None

    settings = get_settings()
    db_path = settings.duckdb_path
    copa_json = Path("data/samples/worldcup2026_copa.json")
    total = 3

    try:
        # ── Etapa 1: ingestão ────────────────────────────────────────────────
        _write_status(status_path, "running", "Ingerindo resultados do worldcup...", 0, total)
        print("1/3 Ingerindo worldcup...", flush=True)
        if not copa_json.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {copa_json}")
        with DuckDBRepository(db_path) as repo:
            result = ingest_worldcup(repo, str(copa_json))
        print(f"   Times: {result.teams}  Partidas: {result.matches}  Snapshot: {result.snapshot_id}", flush=True)

        # ── Etapa 2: backtest ────────────────────────────────────────────────
        _write_status(status_path, "running", "Recalculando scores do bolão...", 1, total)
        print("2/3 Recalculando scores...", flush=True)
        with DuckDBRepository(db_path) as repo:
            summary = run_backtest(repo)
        print(f"   Preditores: {len(summary.standings)}  Partidas avaliadas: {summary.matches_evaluated}", flush=True)

        # ── Etapa 3: export ──────────────────────────────────────────────────
        _write_status(status_path, "running", "Exportando snapshot do portal...", 2, total)
        print("3/3 Exportando portal...", flush=True)
        subprocess.run(
            [sys.executable, str(Path("scripts/export_portal_data.py"))],
            cwd=Path.cwd(),
            check=False,
        )

        now = datetime.now(UTC).strftime("%H:%M") + " UTC"
        _write_status(status_path, "completed", f"Dados atualizados às {now}", total, total)
        print(f"Concluído às {now}.", flush=True)

    except Exception as exc:  # pragma: no cover
        _write_status(status_path, "failed", f"Erro: {exc}", 0, total)
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
