"""Testes dos analytics derivados dos CSVs FIFA."""

from __future__ import annotations

from copamind.data.fifa_analytics import key_players_analytics, matchup_analytics, team_analytics
from copamind.data.fifa_stats import team_rows


def test_team_csvs_are_read_with_semicolon_headers() -> None:
    row = team_rows("attack")[0]

    assert "team_external_id" in row
    assert "goals" in row
    assert ";" not in next(iter(row))


def test_team_analytics_builds_normalized_indexes() -> None:
    analytics = team_analytics("T-FRA")
    indexes = analytics["indexes"]

    assert analytics["team_name"] == "França"
    assert 0 <= indexes["attack_index"] <= 1
    assert 0 <= indexes["defense_index"] <= 1
    assert 0 <= indexes["discipline_risk"] <= 1
    assert 0 <= indexes["champion_profile_score"] <= 1
    assert indexes["champion_profile_score"] != indexes["attack_index"]
    assert analytics["evidence"]


def test_matchup_analytics_exposes_deltas_and_upset_risk() -> None:
    analytics = matchup_analytics("T-FRA", "T-MAR")

    assert analytics["schema_version"] == "copamind.fifa_analytics.v2"
    assert "attack_index" in analytics["deltas"]
    assert 0 <= analytics["upset_risk_score"] <= 1
    assert any(item["id"] == "matchup.upset_risk" for item in analytics["top_evidence"])


def test_key_players_have_roles_and_sample_confidence() -> None:
    players = key_players_analytics("T-FRA", limit=8)

    assert players
    assert all(player["role"] for player in players)
    assert all(0 <= player["confidence"] <= 1 for player in players)
    assert all(player["sample"] in {"normal", "small", "unknown_minutes"} for player in players)
    assert all(player["per90"]["goals"] <= 3 for player in players)
