"""Testes da base ML/RAG por partida."""

from __future__ import annotations

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import MatchStage
from copamind.features.match_features import KNOCKOUT_PHASES, refresh_knockout_feature_snapshots


def test_refresh_knockout_feature_snapshots_filters_final_phases(
    seeded_repo: DuckDBRepository,
) -> None:
    match = seeded_repo.list_finished_matches()[-1].model_copy(
        update={"match_id": "fifa:test-feature", "stage": MatchStage.round_of_16}
    )
    seeded_repo.upsert_matches([match])

    rows = refresh_knockout_feature_snapshots(seeded_repo)

    assert rows
    assert {row["phase"] for row in rows}.issubset(set(KNOCKOUT_PHASES))
    assert seeded_repo.count("match_feature_snapshots") == len(rows)
    assert rows[0]["features"]["anti_leakage"]
    assert "available" in rows[0]["baseline"]
