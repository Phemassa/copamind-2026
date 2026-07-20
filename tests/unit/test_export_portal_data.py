"""Testes do snapshot usado pelo portal estatico."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from scripts.export_portal_data import (
    PHASE_ORDER,
    _build_groups,
    _build_phase_model_scores,
    _build_phase_predictions_by_model,
    _build_phases,
    _resolve_prediction_result,
    _results_by_phase_and_teams,
)


def _team(team_id: str) -> SimpleNamespace:
    return SimpleNamespace(team_id=team_id)


def _match(
    match_id: str,
    home_team_id: str,
    away_team_id: str,
    home_score: int | None,
    away_score: int | None,
    *,
    date: datetime,
    stage: str = "group",
    status: str = "finished",
) -> SimpleNamespace:
    return SimpleNamespace(
        match_id=match_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=home_score,
        away_score=away_score,
        match_date=date,
        stage=stage,
        status=status,
    )


def test_build_groups_calculates_table_and_last5() -> None:
    teams = [_team("T-MEX"), _team("T-RSA"), _team("T-KOR"), _team("T-CZE")]
    matches = [
        _match("m1", "T-MEX", "T-RSA", 2, 0, date=datetime(2026, 6, 1, tzinfo=UTC)),
        _match("m2", "T-KOR", "T-CZE", 1, 1, date=datetime(2026, 6, 2, tzinfo=UTC)),
        _match("m3", "T-MEX", "T-KOR", 1, 1, date=datetime(2026, 6, 3, tzinfo=UTC)),
        _match("m4", "T-RSA", "T-CZE", 3, 1, date=datetime(2026, 6, 4, tzinfo=UTC)),
    ]

    groups = _build_groups(teams, matches)
    group_a = next(group for group in groups if group["group"] == "A")
    mexico = group_a["rows"][0]
    rsa = next(row for row in group_a["rows"] if row["team_id"] == "T-RSA")

    assert mexico["team_id"] == "T-MEX"
    assert mexico["pts"] == 4
    assert mexico["pj"] == 2
    assert mexico["vit"] == 1
    assert mexico["e"] == 1
    assert mexico["der"] == 0
    assert mexico["gm"] == 3
    assert mexico["gc"] == 1
    assert mexico["sg"] == 2
    assert mexico["last5"] == ["W", "D"]
    assert rsa["last5"] == ["L", "W"]


def test_phase_scores_ignore_unscored_predictions() -> None:
    predictions = [
        {
            "phase": "round_of_16",
            "phase_label": "Oitavas",
            "predictor_name": "llm:model-a:round:1",
            "points": 7,
            "winner_hit": True,
            "exact_score": True,
            "brier": 0.12,
        },
        {
            "phase": "round_of_16",
            "phase_label": "Oitavas",
            "predictor_name": "llm:model-a:round:1",
            "points": None,
            "winner_hit": None,
            "exact_score": None,
            "brier": None,
        },
    ]

    scores = _build_phase_model_scores(predictions)

    assert scores[0]["predictions"] == 2
    assert scores[0]["scored"] == 1
    assert scores[0]["points"] == 7
    assert scores[0]["accuracy"] == 1
    assert scores[0]["exact_rate"] == 1
    assert scores[0]["brier_avg"] == 0.12


def test_phase_predictions_by_model_keeps_awaiting_games() -> None:
    predictions = [
        {
            "phase": "final",
            "phase_label": "Final",
            "predictor_name": "combo:llm_pool:round:1",
            "match_date": datetime(2026, 7, 19, tzinfo=UTC),
            "points": None,
        }
    ]

    grouped = _build_phase_predictions_by_model(predictions)

    assert grouped[0]["phase"] == "final"
    assert grouped[0]["model_id"] == "combo"
    assert grouped[0]["predictions"][0]["points"] is None


def test_export_phase_order_is_final_knockout_only() -> None:
    matches = [
        _match(
            "g1",
            "T-MEX",
            "T-RSA",
            None,
            None,
            date=datetime(2026, 6, 1, tzinfo=UTC),
            stage="group",
            status="scheduled",
        ),
        _match(
            "r16",
            "T-MEX",
            "T-RSA",
            None,
            None,
            date=datetime(2026, 7, 1, tzinfo=UTC),
            stage="round_of_16",
            status="scheduled",
        ),
    ]

    phases = _build_phases(matches, [])

    assert PHASE_ORDER == ("round_of_16", "quarterfinal", "semifinal", "third_place", "final")
    assert [phase["key"] for phase in phases] == list(PHASE_ORDER)
    assert phases[0]["match_ids"] == ["r16"]


def test_projected_results_require_same_phase_and_matchup() -> None:
    third_place = _match(
        "third",
        "T-FRA",
        "T-ENG",
        4,
        6,
        date=datetime(2026, 7, 18, tzinfo=UTC),
        stage="third_place",
    )
    final = _match(
        "final",
        "T-ESP",
        "T-ARG",
        1,
        0,
        date=datetime(2026, 7, 19, tzinfo=UTC),
        stage="final",
    )
    third_result = SimpleNamespace(match_id="third")
    final_result = SimpleNamespace(match_id="final")
    results = {"third": third_result, "final": final_result}
    indexed = _results_by_phase_and_teams(
        results,
        {"third": third_place, "final": final},
    )

    correct_final = SimpleNamespace(
        match_id="projected:final:model-a:0",
        home_team_id="T-ESP",
        away_team_id="T-ARG",
    )
    wrong_phase = SimpleNamespace(
        match_id="projected:third_place:model-a:0",
        home_team_id="T-ESP",
        away_team_id="T-ARG",
    )

    assert _resolve_prediction_result(correct_final, results, indexed) is final_result
    assert _resolve_prediction_result(wrong_phase, results, indexed) is None
