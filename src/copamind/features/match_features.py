"""Feature snapshots para o bolao de mata-mata das LLMs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match
from copamind.pool.llm_agent import build_match_context

KNOCKOUT_PHASES = ("round_of_16", "quarterfinal", "semifinal", "third_place", "final")
PHASE_CONTEXT = {
    "round_of_16": (
        "Dados de grupos e fases anteriores entram como historico; "
        "a previsao comeca nas oitavas."
    ),
    "quarterfinal": "Oitavas ja podem calibrar forma recente, gols e estabilidade das LLMs.",
    "semifinal": "Todo o caminho ate as quartas entra no contexto pre-jogo.",
    "third_place": (
        "Disputa de 3o lugar usa todo o mata-mata anterior, "
        "com motivacao e rotacao como incertezas."
    ),
    "final": "Final do titulo usa todo o mata-mata disponivel no contexto pre-jogo.",
}


def refresh_knockout_feature_snapshots(repo: DuckDBRepository) -> list[dict[str, Any]]:
    """Recalcula snapshots ML/RAG para Oitavas, Quartas, Semifinais e Final."""
    repo.create_schema()
    matches = [
        match
        for match in repo.list_matches(limit=800)
        if str(match.stage) in KNOCKOUT_PHASES and str(match.match_id).startswith("fifa:")
    ]
    matches.sort(key=lambda item: (item.match_date, item.match_id))
    refreshed: list[dict[str, Any]] = []
    for match in matches:
        refreshed.append(upsert_match_feature_snapshot(repo, match))
    return refreshed


def upsert_match_feature_snapshot(repo: DuckDBRepository, match: Match) -> dict[str, Any]:
    """Cria/atualiza o snapshot estatistico de uma partida."""
    context = build_match_context(repo, match)
    baseline = context.get("statistical_baseline") or {}
    analytics = context.get("analytics") or {}
    features = {
        "schema_version": "copamind.match_features.v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "as_of": match.match_date.isoformat(),
        "phase": str(match.stage),
        "phase_context": PHASE_CONTEXT.get(str(match.stage), "Contexto historico disponivel."),
        "anti_leakage": (
            "Somente partidas com available_at <= match_date entram "
            "na forma recente e baseline."
        ),
        "fixture": context["match"],
        "matchup_summary": analytics.get("summary"),
        "matchup_deltas": analytics.get("deltas", {}),
        "upset_risk_score": analytics.get("upset_risk_score"),
        "top_evidence": analytics.get("top_evidence", []),
        "teams": {
            "home": context["home"],
            "away": context["away"],
        },
        "evidence": context["evidence"],
        "uncertainty": _uncertainty_notes(context),
    }
    snapshot_id = f"mlfeat:{match.match_id}:{match.match_date.strftime('%Y%m%d%H%M')}"
    created_at = datetime.now(UTC)
    repo.upsert_match_feature_snapshot(
        snapshot_id=snapshot_id,
        match_id=match.match_id,
        phase=str(match.stage),
        as_of=match.match_date,
        features=features,
        baseline=baseline,
        created_at=created_at,
    )
    return {
        "snapshot_id": snapshot_id,
        "match_id": match.match_id,
        "phase": str(match.stage),
        "as_of": match.match_date,
        "created_at": created_at,
        "features": features,
        "baseline": baseline,
    }


def _uncertainty_notes(context: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    baseline = context.get("statistical_baseline") or {}
    if not baseline.get("available"):
        notes.append(str(baseline.get("reason") or "Baseline estatistico indisponivel."))
    for side in ("home", "away"):
        team = context.get(side, {})
        if not team.get("recent_form"):
            notes.append(
                f"{team.get('team_name', side)} sem forma recente suficiente antes do jogo."
            )
        if not team.get("key_players"):
            notes.append(f"{team.get('team_name', side)} sem jogadores-chave nos CSVs FIFA.")
    return notes or ["Contexto suficiente; imprevisibilidade normal de mata-mata."]
