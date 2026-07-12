"""Exporta um snapshot JSON para o portal web estatico."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from copamind.core.config import get_settings
from copamind.data.connectors.flags import TEAMS
from copamind.data.fifa_analytics import key_players_analytics, team_analytics
from copamind.data.fifa_match_extras import match_extra
from copamind.data.fifa_stats import available_summary, flag_url, player_metric_leaders, team_label
from copamind.data.repositories import DuckDBRepository
from copamind.features.match_features import KNOCKOUT_PHASES, refresh_knockout_feature_snapshots
from copamind.llm.client import LLMError, LMStudioClient
from copamind.pool.llm_agent import classify_local_model
from copamind.pool.scoring import brier_score, outcome
from copamind.pool.service import leaderboard

OUTPUT_PATH = Path("apps/portal/data/copamind.json")
PHASE_ORDER = KNOCKOUT_PHASES
PHASE_LABELS = {
    "group": "Grupos",
    "round_of_32": "16 avos",
    "round_of_16": "Oitavas",
    "quarterfinal": "Quartas",
    "semifinal": "Semifinais",
    "third_place": "3o lugar",
    "final": "Final",
}
TOURNAMENT_STAGE_ORDER = ("group", "round_of_32", "round_of_16", "quarterfinal", "semifinal", "third_place", "final")
MODEL_IMAGES = {
    "combo": "",
    # Google
    "gemma": "https://cdn.simpleicons.org/googlegemini/4285F4",
    # Alibaba / Qwen
    "qwen": "https://qwenlm.github.io/img/logo.png",
    # Mistral AI
    "mistral": "https://cdn.simpleicons.org/mistralai/FA520F",
    "ministral": "https://cdn.simpleicons.org/mistralai/FA520F",
    # Microsoft
    "phi": "../../pictures/icons/phi.png",
    "microsoft": "../../pictures/icons/phi.png",
    # Zhipu AI / ZAI
    "glm": "../../pictures/icons/glm.png",
    # Meta
    "llama": "https://cdn.simpleicons.org/meta/0081FB",
    # NVIDIA
    "nvidia": "https://cdn.simpleicons.org/nvidia/76B900",
    "nemotron": "https://cdn.simpleicons.org/nvidia/76B900",
    # OpenAI
    "openai": "../../pictures/icons/gpt.png",
    # DeepSeek
    "deepseek": "https://cdn.simpleicons.org/deepseek/4D6BFF",
    # IBM
    "ibm": "../../pictures/icons/granite.png",
    "granite": "../../pictures/icons/granite.png",
    # Baidu
    "baidu": "https://cdn.simpleicons.org/baidu/2932E1",
    "ernie": "https://cdn.simpleicons.org/baidu/2932E1",
    # AllenAI
    "allenai": "../../pictures/icons/olm.png",
    "olmo": "../../pictures/icons/olm.png",
    # ByteDance
    "bytedance": "../../pictures/icons/oss.png",
    "seed": "../../pictures/icons/oss.png",
    # Essential AI
    "essentialai": "https://essential.ai/favicon.ico",
    "rnj": "https://essential.ai/favicon.ico",
    # Liquid AI
    "liquid": "../../pictures/icons/lfm2.png",
    "lfm": "../../pictures/icons/lfm2.png",
}


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DuckDBRepository(get_settings().duckdb_path) as repo:
        repo.create_schema()
        payload = _build_payload(repo)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    print(f"Portal data exported to {OUTPUT_PATH}")


def _build_payload(repo: DuckDBRepository) -> dict[str, Any]:
    refresh_knockout_feature_snapshots(repo)
    teams = repo.list_teams()
    all_matches = repo.list_matches(limit=800)
    knockout_matches = [
        match
        for match in all_matches
        if str(match.stage) in PHASE_ORDER and str(match.match_id).startswith("fifa:")
    ]
    predictions = repo.list_pool_predictions()
    payloads = {item["prediction_id"]: item["payload"] for item in repo.list_pool_prediction_payloads()}
    results = {item.match_id: item for item in repo.list_pool_results()}
    matches_by_id = {match.match_id: match for match in knockout_matches}
    standings = leaderboard(repo)
    consensus = repo.list_llm_model_consensus()
    runs = repo.list_llm_model_runs()
    model_metrics = repo.llm_model_metrics()
    rounds = repo.list_llm_pool_rounds()
    batches = repo.list_llm_phase_batches()
    feature_snapshots = _feature_snapshot_payloads(
        repo.list_match_feature_snapshots(),
        allowed_match_ids={match.match_id for match in knockout_matches},
    )
    context_notes = _context_note_payloads(repo.list_team_context_notes(active_only=False))
    serialized_matches = [_match_payload(match) for match in sorted(knockout_matches, key=lambda item: item.match_date)]
    tournament_matches = [
        _match_payload(match)
        for match in sorted(
            [item for item in all_matches if str(item.match_id).startswith("fifa:")],
            key=lambda item: (
                TOURNAMENT_STAGE_ORDER.index(str(item.stage)) if str(item.stage) in TOURNAMENT_STAGE_ORDER else 99,
                item.match_date,
                item.match_id,
            ),
        )
    ]
    serialized_predictions_all = [
        _prediction_payload(
            item,
            matches_by_id.get(item.match_id),
            results.get(item.match_id),
            payloads.get(item.prediction_id, {}),
        )
        for item in predictions
        if item.match_id in matches_by_id or str(item.match_id).startswith("projected:")
    ]
    serialized_predictions = _latest_model_match_predictions(serialized_predictions_all)
    phases = _build_phases(knockout_matches, serialized_predictions)
    phase_model_scores = _build_phase_model_scores(serialized_predictions)
    phase_predictions_by_model = _build_phase_predictions_by_model(serialized_predictions, knockout_matches)
    phase_model_run_status = _build_phase_model_run_status(runs, rounds, matches_by_id)
    model_cards = _build_models(
        model_metrics,
        phase_model_scores,
        phase_predictions_by_model,
        available_model_ids=_available_lmstudio_models(),
    )
    return {
        "generated_at": datetime.now(UTC),
        "sync_status": {
            "latest_snapshot_id": repo.latest_snapshot_id(),
            "feature_snapshots": len(feature_snapshots),
            "knockout_phases": list(PHASE_ORDER),
        },
        "summary": {
            "teams": len(teams),
            "matches": len(knockout_matches),
            "scheduled": sum(1 for match in knockout_matches if str(match.status) == "scheduled"),
            "finished": sum(1 for match in knockout_matches if str(match.status) == "finished"),
            "predictions": len(predictions),
            "rounds": len(rounds),
            "batches": len(batches),
            **available_summary(),
        },
        "teams": [
            {
                "team_id": team.team_id,
                "name": team_label(team.team_id),
                "fifa_code": team.fifa_code,
                "group": TEAMS.get(team.team_id, {}).get("group", ""),
                "flag_url": flag_url(team.team_id),
                "elo_rating": team.elo_rating,
                "fifa_ranking": team.fifa_ranking,
                "analytics": team_analytics(team.team_id),
                "key_players": key_players_analytics(team.team_id, limit=5),
            }
            for team in teams
        ],
        "matches": serialized_matches,
        "tournament": {
            "groups": _build_groups(teams, all_matches),
            "matches": tournament_matches,
            "stage_order": list(TOURNAMENT_STAGE_ORDER),
            "stage_labels": {stage: PHASE_LABELS.get(stage, stage) for stage in TOURNAMENT_STAGE_ORDER},
        },
        "phases": phases,
        "models": model_cards,
        "feature_snapshots": feature_snapshots,
        "context_notes": context_notes,
        "phase_model_scores": phase_model_scores,
        "phase_model_run_status": phase_model_run_status,
        "phase_predictions_by_model": phase_predictions_by_model,
        "leaderboard": [
            {
                "predictor_name": item.predictor_name,
                "points": item.total_points,
                "predictions": item.predictions,
                "mean_brier": item.mean_brier,
            }
            for item in standings
        ],
        "predictions": serialized_predictions,
        "players": _build_players(teams),
        "llm": {
            "rounds": rounds,
            "batches": batches,
            "consensus": consensus,
            "runs": runs,
            "model_metrics": model_metrics,
        },
    }


def _build_players(teams: list[Any]) -> list[dict[str, Any]]:
    """Monta ranking consolidado de jogadores para o portal."""
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    code_to_team_id = {team.fifa_code: team.team_id for team in teams}
    for team in teams:
        for player in key_players_analytics(team.team_id, limit=12):
            key = (str(player.get("player_id") or ""), str(player.get("team_code") or team.fifa_code))
            if not key[0]:
                continue
            by_key[key] = _player_dashboard_card(player, team.team_id)
    for player in player_metric_leaders("scorers", "goals", limit=160):
        team_id = code_to_team_id.get(str(player.get("team_code") or ""))
        if not team_id:
            continue
        key = (str(player.get("player_id") or ""), str(player.get("team_code") or ""))
        current = by_key.get(key)
        if current:
            current["goals"] = player.get("goals", current.get("goals", 0))
            current["assists"] = player.get("assists", current.get("assists", 0))
            current["minutes"] = max(float(current.get("minutes") or 0), float(player.get("minutes") or 0))
            current["impact_score"] = round(float(current.get("impact_score") or 0) + float(player.get("goals") or 0) * 2, 3)
            continue
        by_key[key] = {
            "player_id": player.get("player_id"),
            "name": player.get("name"),
            "team": player.get("team"),
            "team_id": team_id,
            "team_code": player.get("team_code"),
            "position": player.get("position"),
            "image_url": player.get("image_url"),
            "flag_url": player.get("flag_url"),
            "role": "finalizador",
            "role_score": round(float(player.get("goals") or 0), 3),
            "reason": "gols marcados",
            "confidence": 0.65,
            "sample": "ranking_gols",
            "minutes": player.get("minutes", 0),
            "goals": player.get("goals", 0),
            "assists": player.get("assists", 0),
            "per90": {
                "goals": _per90(float(player.get("goals") or 0), float(player.get("minutes") or 0)),
                "assists": _per90(float(player.get("assists") or 0), float(player.get("minutes") or 0)),
                "shots_on_target": _per90(float(player.get("shots_on_target") or 0), float(player.get("minutes") or 0)),
            },
            "impact_score": round(float(player.get("goals") or 0) * 10 + float(player.get("assists") or 0) * 4, 3),
        }
    players = list(by_key.values())
    players.sort(
        key=lambda item: (
            float(item.get("impact_score") or 0),
            float(item.get("confidence") or 0),
            float(item.get("minutes") or 0),
        ),
        reverse=True,
    )
    return players[:240]


def _player_dashboard_card(player: dict[str, Any], team_id: str) -> dict[str, Any]:
    per90 = player.get("per90") if isinstance(player.get("per90"), dict) else {}
    goals_p90 = float(per90.get("goals") or 0)
    assists_p90 = float(per90.get("assists") or 0)
    shots_p90 = float(per90.get("shots_on_target") or 0)
    xg_p90 = float(per90.get("xg") or 0)
    role_score = float(player.get("role_score") or 0)
    confidence = float(player.get("confidence") or 0)
    impact = confidence * 60 + min(role_score / 3, 1) * 25 + goals_p90 * 4 + assists_p90 * 3 + shots_p90 + xg_p90 * 2
    return {
        **player,
        "team_id": team_id,
        "goals": 0,
        "assists": 0,
        "impact_score": round(impact, 3),
    }


def _per90(value: float, minutes: float) -> float:
    if minutes <= 0:
        return round(value, 3)
    return round(value * 90 / minutes, 3)


def _match_payload(match: Any) -> dict[str, Any]:
    extra = match_extra(match.match_id)
    return {
        "match_id": match.match_id,
        "stage": str(match.stage),
        "date": match.match_date,
        "home_team_id": match.home_team_id,
        "away_team_id": match.away_team_id,
        "home": team_label(match.home_team_id),
        "away": team_label(match.away_team_id),
        "home_flag_url": flag_url(match.home_team_id),
        "away_flag_url": flag_url(match.away_team_id),
        "home_score": match.home_score,
        "away_score": match.away_score,
        "home_penalty_score": extra.get("home_penalty_score"),
        "away_penalty_score": extra.get("away_penalty_score"),
        "went_to_extra_time": bool(extra.get("went_to_extra_time")),
        "went_to_penalties": bool(extra.get("went_to_penalties")),
        "winner_side": extra.get("winner_side"),
        "status": str(match.status),
    }


def _prediction_payload(
    prediction: Any,
    match: Any | None,
    result: Any | None,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pick_payload = _pick_payload(raw_payload or {})
    phase = _phase_from_prediction(prediction, match)
    payload = {
        "prediction_id": prediction.prediction_id,
        "predictor_name": prediction.predictor_name,
        "model_id": _model_id_from_predictor(prediction.predictor_name),
        "is_combo": str(prediction.predictor_name).startswith("combo:"),
        "match_id": prediction.match_id,
        "phase": phase,
        "phase_label": PHASE_LABELS.get(phase, phase),
        "home": team_label(prediction.home_team_id),
        "away": team_label(prediction.away_team_id),
        "home_team_id": prediction.home_team_id,
        "away_team_id": prediction.away_team_id,
        "match_date": match.match_date if match is not None else None,
        "prob_home": prediction.prob_home,
        "prob_draw": prediction.prob_draw,
        "prob_away": prediction.prob_away,
        "predicted_home_goals": prediction.predicted_home_goals,
        "predicted_away_goals": prediction.predicted_away_goals,
        "goes_to_extra_time": bool(pick_payload.get("goes_to_extra_time")),
        "goes_to_penalties": bool(pick_payload.get("goes_to_penalties")),
        "penalty_winner": pick_payload.get("penalty_winner") or "none",
        "first_goal_scorer": pick_payload.get("first_goal_scorer"),
        "player_picks": pick_payload.get("player_picks") if isinstance(pick_payload.get("player_picks"), list) else [],
        "confidence": pick_payload.get("confidence"),
        "locked_at": prediction.locked_at,
    }
    return payload | _prediction_result(prediction, result, pick_payload, match)


def _phase_from_prediction(prediction: Any, match: Any | None) -> str:
    if match is not None:
        return str(match.stage)
    match_id = str(prediction.match_id)
    if match_id.startswith("projected:"):
        parts = match_id.split(":", 3)
        if len(parts) >= 2:
            return parts[1]
    return ""


def _prediction_result(
    prediction: Any,
    result: Any | None,
    pick_payload: dict[str, Any],
    match: Any | None,
) -> dict[str, Any]:
    extra = match_extra(match.match_id) if match is not None else {}
    if result is None:
        return {
            "points": None,
            "brier": None,
            "winner_hit": None,
            "exact_score": None,
            "actual_home_goals": None,
            "actual_away_goals": None,
            "actual_home_penalty_score": extra.get("home_penalty_score"),
            "actual_away_penalty_score": extra.get("away_penalty_score"),
            "actual_extra_time": bool(extra.get("went_to_extra_time")),
            "actual_penalties": bool(extra.get("went_to_penalties")),
            "actual_winner": extra.get("winner_side"),
            "status": "awaiting",
        }
    actual = _actual_knockout_outcome(result.home_score, result.away_score, extra)
    predicted = _predicted_knockout_outcome(prediction, pick_payload)
    exact_score = (
        prediction.predicted_home_goals == result.home_score
        and prediction.predicted_away_goals == result.away_score
        and predicted == actual
    )
    return {
        "points": POINTS_EXACT_SCORE if exact_score else POINTS_CORRECT_RESULT if predicted == actual else 0,
        "brier": brier_score(
            prediction.prob_home,
            prediction.prob_draw,
            prediction.prob_away,
            actual,
        ),
        "winner_hit": predicted == actual,
        "exact_score": exact_score,
        "actual_home_goals": result.home_score,
        "actual_away_goals": result.away_score,
        "actual_home_penalty_score": extra.get("home_penalty_score"),
        "actual_away_penalty_score": extra.get("away_penalty_score"),
        "actual_extra_time": bool(extra.get("went_to_extra_time")),
        "actual_penalties": bool(extra.get("went_to_penalties")),
        "actual_winner": actual,
        "status": "scored",
    }


POINTS_EXACT_SCORE = 5
POINTS_CORRECT_RESULT = 3


def _actual_knockout_outcome(home_score: int, away_score: int, extra: dict[str, Any]) -> str:
    if home_score != away_score:
        return outcome(home_score, away_score)
    winner = extra.get("winner_side")
    return str(winner) if winner in {"home", "away"} else "draw"


def _predicted_knockout_outcome(prediction: Any, pick_payload: dict[str, Any]) -> str:
    if prediction.predicted_home_goals != prediction.predicted_away_goals:
        return outcome(prediction.predicted_home_goals, prediction.predicted_away_goals)
    penalty_winner = pick_payload.get("penalty_winner")
    if penalty_winner in {"home", "away"}:
        return str(penalty_winner)
    winner = pick_payload.get("winner")
    return str(winner) if winner in {"home", "away"} else "draw"


def _build_groups(teams: list[Any], matches: list[Any]) -> list[dict[str, Any]]:
    rows_by_group: dict[str, dict[str, dict[str, Any]]] = {}
    for team in teams:
        group = TEAMS.get(team.team_id, {}).get("group", "")
        if not group:
            continue
        rows_by_group.setdefault(group, {})[team.team_id] = {
            "team_id": team.team_id,
            "team": team_label(team.team_id),
            "flag_url": flag_url(team.team_id),
            "pts": 0,
            "pj": 0,
            "vit": 0,
            "e": 0,
            "der": 0,
            "gm": 0,
            "gc": 0,
            "sg": 0,
            "last5": [],
        }

    group_matches = [match for match in matches if str(match.stage) == "group"]
    group_matches.sort(key=lambda match: (match.match_date, match.match_id))
    for match in group_matches:
        if str(match.status) != "finished" or match.home_score is None or match.away_score is None:
            continue
        home_group = TEAMS.get(match.home_team_id, {}).get("group", "")
        away_group = TEAMS.get(match.away_team_id, {}).get("group", "")
        if not home_group or home_group != away_group:
            continue
        home = rows_by_group.setdefault(home_group, {}).get(match.home_team_id)
        away = rows_by_group.setdefault(away_group, {}).get(match.away_team_id)
        if home is None or away is None:
            continue
        _apply_group_result(home, match.home_score, match.away_score)
        _apply_group_result(away, match.away_score, match.home_score)
        home["last5"].append(_form_token(match.home_score, match.away_score))
        away["last5"].append(_form_token(match.away_score, match.home_score))

    groups = []
    for group, rows_by_team in sorted(rows_by_group.items()):
        rows = sorted(
            rows_by_team.values(),
            key=lambda row: (-row["pts"], -row["sg"], -row["gm"], row["team"]),
        )
        for index, row in enumerate(rows, 1):
            row["rank"] = index
            row["last5"] = row["last5"][-5:]
        groups.append({"group": group, "label": f"Grupo {group}", "rows": rows})
    return groups


def _apply_group_result(row: dict[str, Any], goals_for: int, goals_against: int) -> None:
    row["pj"] += 1
    row["gm"] += goals_for
    row["gc"] += goals_against
    row["sg"] = row["gm"] - row["gc"]
    if goals_for > goals_against:
        row["vit"] += 1
        row["pts"] += 3
    elif goals_for == goals_against:
        row["e"] += 1
        row["pts"] += 1
    else:
        row["der"] += 1


def _form_token(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "W"
    if goals_for == goals_against:
        return "D"
    return "L"


def _build_phases(matches: list[Any], predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predictions_by_phase: dict[str, list[dict[str, Any]]] = {}
    for prediction in predictions:
        predictions_by_phase.setdefault(str(prediction.get("phase") or ""), []).append(prediction)
    phases = []
    for phase in PHASE_ORDER:
        phase_matches = [match for match in matches if str(match.stage) == phase]
        phase_matches.sort(key=lambda match: (match.match_date, match.match_id))
        phase_predictions = predictions_by_phase.get(phase, [])
        phases.append(
            {
                "key": phase,
                "label": PHASE_LABELS[phase],
                "context": _phase_context(phase),
                "match_ids": [match.match_id for match in phase_matches],
                "match_count": len(phase_matches),
                "finished_count": sum(1 for match in phase_matches if str(match.status) == "finished"),
                "prediction_count": len(phase_predictions),
                "models_count": len(
                    {
                        str(item.get("model_id") or _model_id_from_predictor(str(item.get("predictor_name") or "")))
                        for item in phase_predictions
                    }
                ),
            }
        )
    return phases


def _phase_context(phase: str) -> str:
    previous = {
        "round_of_16": "Base FIFA, classificacao e historico anterior entram no contexto pre-jogo.",
        "quarterfinal": "Oitavas e dados FIFA calibram forma recente, gols e incertezas.",
        "semifinal": "Todo o caminho ate as quartas entra no contexto pre-jogo.",
        "third_place": "Disputa de 3o lugar usa caminho ate semifinais, desgaste e motivacao.",
        "final": "Final do titulo usa todo o mata-mata disponivel no contexto pre-jogo.",
    }
    return previous[phase]


def _build_phase_model_scores(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for prediction in _llm_predictions(predictions):
        model_id = str(prediction.get("model_id") or _model_id_from_predictor(prediction["predictor_name"]))
        key = (prediction["phase"], model_id)
        item = grouped.setdefault(
            key,
            {
                "phase": prediction["phase"],
                "phase_label": prediction["phase_label"],
                "model_id": model_id,
                "display_name": _display_model_name(model_id),
                "is_combo": bool(prediction.get("is_combo")),
                "predictions": 0,
                "scored": 0,
                "points": 0,
                "winner_hits": 0,
                "exact_hits": 0,
                "brier_sum": 0.0,
            },
        )
        item["predictions"] += 1
        if prediction["points"] is None:
            continue
        item["scored"] += 1
        item["points"] += int(prediction["points"])
        item["winner_hits"] += int(bool(prediction["winner_hit"]))
        item["exact_hits"] += int(bool(prediction["exact_score"]))
        item["brier_sum"] += float(prediction["brier"] or 0)
    scores = []
    for item in grouped.values():
        scored = int(item["scored"])
        scores.append(
            item
            | {
                "accuracy": item["winner_hits"] / scored if scored else None,
                "exact_rate": item["exact_hits"] / scored if scored else None,
                "brier_avg": item["brier_sum"] / scored if scored else None,
            }
        )
    return sorted(
        scores,
        key=lambda item: (
            PHASE_ORDER.index(item["phase"]) if item["phase"] in PHASE_ORDER else 99,
            -(item["accuracy"] if item["accuracy"] is not None else -1),
            -item["points"],
            item["model_id"],
        ),
    )


def _build_phase_predictions_by_model(
    predictions: list[dict[str, Any]],
    matches: list[Any] | None = None,
) -> list[dict[str, Any]]:
    matches_by_phase: dict[str, list[Any]] = {}
    for match in matches or []:
        matches_by_phase.setdefault(str(match.stage), []).append(match)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for prediction in _llm_predictions(predictions):
        model_id = str(prediction.get("model_id") or _model_id_from_predictor(prediction["predictor_name"]))
        grouped.setdefault((prediction["phase"], model_id), []).append(prediction)
    rows = []
    for (phase, model_id), items in grouped.items():
        completed_items = _complete_phase_predictions(phase, model_id, items, matches_by_phase.get(phase, []))
        rows.append(
            {
                "phase": phase,
                "phase_label": PHASE_LABELS.get(phase, phase),
                "model_id": model_id,
                "display_name": _display_model_name(model_id),
                "is_combo": model_id == "combo",
                "predictions": sorted(completed_items, key=lambda item: str(item.get("match_date") or "")),
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            PHASE_ORDER.index(item["phase"]) if item["phase"] in PHASE_ORDER else 99,
            item["model_id"],
        ),
    )


def _build_phase_model_run_status(
    runs: list[dict[str, Any]],
    rounds: list[dict[str, Any]],
    matches_by_id: dict[str, Any],
) -> list[dict[str, Any]]:
    round_phase: dict[str, str] = {}
    for row in rounds:
        match = matches_by_id.get(str(row.get("match_id") or ""))
        phase = str(row.get("phase") or (match.stage if match is not None else ""))
        if phase in PHASE_ORDER:
            round_phase[str(row.get("round_id") or "")] = phase

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for run in runs:
        phase = round_phase.get(str(run.get("round_id") or ""))
        if phase not in PHASE_ORDER:
            continue
        model_id = str(run.get("model_id") or "")
        if not model_id:
            continue
        if not classify_local_model(model_id).participates:
            continue
        item = grouped.setdefault(
            (phase, model_id),
            {
                "phase": phase,
                "phase_label": PHASE_LABELS.get(phase, phase),
                "model_id": model_id,
                "display_name": _display_model_name(model_id),
                "runs": 0,
                "valid_runs": 0,
                "invalid_runs": 0,
                "error_counts": {},
                "last_error": None,
            },
        )
        item["runs"] += 1
        if run.get("valid"):
            item["valid_runs"] += 1
        else:
            item["invalid_runs"] += 1
            error_type = _run_error_type(str(run.get("error") or ""))
            item["error_counts"][error_type] = int(item["error_counts"].get(error_type, 0)) + 1
            if run.get("error"):
                item["last_error"] = str(run.get("error"))[:240]
    return sorted(grouped.values(), key=lambda item: (PHASE_ORDER.index(item["phase"]), item["model_id"]))


def _run_error_type(error: str) -> str:
    lowered = error.casefold()
    if "lm studio" in lowered or "bad request" in lowered or "http" in lowered:
        return "lmstudio_error"
    if "json" in lowered:
        return "json_invalid"
    if "context" in lowered or "token" in lowered:
        return "context_error"
    return "other_error"


def _complete_phase_predictions(
    phase: str,
    model_id: str,
    predictions: list[dict[str, Any]],
    phase_matches: list[Any],
) -> list[dict[str, Any]]:
    if not phase_matches:
        return [item | {"has_prediction": True} for item in predictions]

    by_match_id = {str(item.get("match_id")): item | {"has_prediction": True} for item in predictions}
    completed: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    for match in sorted(phase_matches, key=lambda item: (item.match_date, item.match_id)):
        mid = str(match.match_id)
        pred = by_match_id.get(mid)
        if pred is not None:
            completed.append(pred)
            used_ids.add(mid)
            continue
        # Fall back: look for a projected prediction with the same team IDs
        proj = next(
            (
                p | {"has_prediction": True}
                for p in predictions
                if str(p.get("match_id", "")).startswith("projected:")
                and p.get("home_team_id") == match.home_team_id
                and p.get("away_team_id") == match.away_team_id
            ),
            None,
        )
        if proj is not None:
            used_ids.add(str(proj.get("match_id", "")))
            completed.append(proj)
        else:
            completed.append(_missing_prediction_payload(phase, model_id, match))

    # Append projected predictions that have no corresponding real match yet
    for pred in predictions:
        pmid = str(pred.get("match_id", ""))
        if pmid.startswith("projected:") and pmid not in used_ids:
            completed.append(pred | {"has_prediction": True, "is_projection": True})

    return completed


def _missing_prediction_payload(phase: str, model_id: str, match: Any) -> dict[str, Any]:
    extra = match_extra(match.match_id)
    return {
        "has_prediction": False,
        "prediction_id": None,
        "predictor_name": "",
        "model_id": model_id,
        "is_combo": model_id == "combo",
        "match_id": match.match_id,
        "phase": phase,
        "phase_label": PHASE_LABELS.get(phase, phase),
        "home": team_label(match.home_team_id),
        "away": team_label(match.away_team_id),
        "home_team_id": match.home_team_id,
        "away_team_id": match.away_team_id,
        "match_date": match.match_date,
        "prob_home": None,
        "prob_draw": None,
        "prob_away": None,
        "predicted_home_goals": None,
        "predicted_away_goals": None,
        "goes_to_extra_time": False,
        "goes_to_penalties": False,
        "penalty_winner": "none",
        "first_goal_scorer": None,
        "confidence": None,
        "locked_at": None,
        "points": None,
        "brier": None,
        "winner_hit": None,
        "exact_score": None,
        "actual_home_goals": match.home_score,
        "actual_away_goals": match.away_score,
        "actual_home_penalty_score": extra.get("home_penalty_score"),
        "actual_away_penalty_score": extra.get("away_penalty_score"),
        "actual_extra_time": bool(extra.get("went_to_extra_time")),
        "actual_penalties": bool(extra.get("went_to_penalties")),
        "status": "missing_prediction",
    }


def _latest_model_match_predictions(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for prediction in _llm_predictions(predictions):
        model_id = str(prediction.get("model_id") or _model_id_from_predictor(prediction["predictor_name"]))
        key = (str(prediction.get("phase") or ""), model_id, str(prediction.get("match_id") or ""))
        previous = latest.get(key)
        if previous is None or str(prediction.get("locked_at") or "") >= str(previous.get("locked_at") or ""):
            latest[key] = prediction | {"model_id": model_id}
    return sorted(
        latest.values(),
        key=lambda item: (
            PHASE_ORDER.index(item["phase"]) if item["phase"] in PHASE_ORDER else 99,
            str(item.get("match_date") or ""),
            item["model_id"],
        ),
    )


def _llm_predictions(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        prediction
        for prediction in predictions
        if prediction.get("phase") in PHASE_ORDER
        and (
            str(prediction.get("predictor_name", "")).startswith("llm:")
            or str(prediction.get("predictor_name", "")).startswith("combo:")
        )
    ]


def _pick_payload(payload: dict[str, Any]) -> dict[str, Any]:
    pick = payload.get("pick")
    if isinstance(pick, dict):
        return pick
    if payload.get("status") == "valid":
        return {
            key: payload.get(key)
            for key in (
                "goes_to_extra_time",
                "goes_to_penalties",
                "penalty_winner",
                "first_goal_scorer",
                "confidence",
            )
            if key in payload
        }
    return {}


def _feature_snapshot_payloads(
    rows: list[dict[str, Any]],
    *,
    allowed_match_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    latest_by_match: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["phase"] not in PHASE_ORDER:
            continue
        if allowed_match_ids is not None and row["match_id"] not in allowed_match_ids:
            continue
        previous = latest_by_match.get(row["match_id"])
        if previous is None or str(row["created_at"]) > str(previous["created_at"]):
            latest_by_match[row["match_id"]] = row
    return [
        {
            "snapshot_id": row["snapshot_id"],
            "match_id": row["match_id"],
            "phase": row["phase"],
            "as_of": row["as_of"],
            "created_at": row["created_at"],
            "baseline": row["baseline"],
            "summary": _feature_summary(row["features"]),
        }
        for row in sorted(latest_by_match.values(), key=lambda item: (item["phase"], item["as_of"]))
    ]


def _context_note_payloads(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "phase_label": PHASE_LABELS.get(str(row.get("phase") or ""), str(row.get("phase") or "")),
            "team_name": team_label(str(row.get("team_id") or "")),
        }
        for row in rows
    ]


def _feature_summary(features: dict[str, Any]) -> dict[str, Any]:
    fixture = features.get("fixture", {})
    teams = features.get("teams", {})
    home = teams.get("home", {})
    away = teams.get("away", {})
    return {
        "schema_version": features.get("schema_version"),
        "fixture": fixture,
        "matchup_summary": features.get("matchup_summary"),
        "matchup_deltas": features.get("matchup_deltas", {}),
        "upset_risk_score": features.get("upset_risk_score"),
        "top_evidence": features.get("top_evidence", []),
        "home_stats": home.get("stats", {}),
        "away_stats": away.get("stats", {}),
        "home_analytics": home.get("analytics", {}),
        "away_analytics": away.get("analytics", {}),
        "home_key_players": home.get("key_players", [])[:6],
        "away_key_players": away.get("key_players", [])[:6],
        "home_recent_form": home.get("recent_form", []),
        "away_recent_form": away.get("recent_form", []),
        "uncertainty": features.get("uncertainty", []),
    }


def _build_models(
    metrics: list[dict[str, Any]],
    phase_scores: list[dict[str, Any]],
    predictions_by_model: list[dict[str, Any]],
    *,
    available_model_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    metric_by_model = {str(item["model_id"]): item for item in metrics}
    model_ids = set(metric_by_model)
    model_ids.update(str(item["model_id"]) for item in phase_scores)
    model_ids.update(str(item["model_id"]) for item in predictions_by_model)
    model_ids.update(available_model_ids or [])
    cards = []
    for model_id in sorted(model_ids, key=lambda value: (value != "combo", value)):
        info = classify_local_model(model_id) if model_id != "combo" else None
        if model_id != "combo" and info is not None and not info.participates:
            continue
        family = _model_family(model_id)
        scores = [item for item in phase_scores if item["model_id"] == model_id]
        scored = sum(int(item["scored"]) for item in scores)
        winner_hits = sum(int(item["winner_hits"]) for item in scores)
        points = sum(int(item["points"]) for item in scores)
        brier_items = [item for item in scores if item["brier_avg"] is not None and item["scored"]]
        brier_weight = sum(int(item["scored"]) for item in brier_items)
        metrics_row = metric_by_model.get(model_id, {})
        cards.append(
            {
                "model_id": model_id,
                "display_name": _display_model_name(model_id),
                "family": family,
                "image_url": _model_image(model_id, family),
                "is_combo": model_id == "combo",
                "available": model_id in set(available_model_ids or []),
                "model_class": info.model_class if info is not None else "combo",
                "telemetry": {
                    "rounds": int(metrics_row.get("total_rounds") or 0),
                    "runs": int(metrics_row.get("total_runs") or 0),
                    "valid_runs": int(metrics_row.get("valid_runs") or 0),
                    "json_rate": (
                        (float(metrics_row.get("valid_runs") or 0) / float(metrics_row.get("total_runs") or 1))
                        if metrics_row.get("total_runs")
                        else None
                    ),
                    "avg_latency_ms": metrics_row.get("avg_latency_ms"),
                    "avg_tokens_per_second": metrics_row.get("avg_tokens_per_second"),
                },
                "overall": {
                    "points": points,
                    "scored": scored,
                    "accuracy": winner_hits / scored if scored else None,
                    "brier_avg": (
                        sum(float(item["brier_avg"]) * int(item["scored"]) for item in brier_items)
                        / brier_weight
                        if brier_weight
                        else None
                    ),
                },
                "phase_scores": list(scores),
            }
        )
    return cards


def _available_lmstudio_models() -> list[str]:
    try:
        model_ids = LMStudioClient(timeout=5).list_models()
    except LLMError:
        return []
    return [
        model_id
        for model_id in model_ids
        if classify_local_model(model_id).participates
    ]


def _model_id_from_predictor(predictor_name: str) -> str:
    value = str(predictor_name)
    if value.startswith("combo:"):
        return "combo"
    if value.startswith("llm:") and ":round:" in value:
        return value.removeprefix("llm:").split(":round:", 1)[0]
    return value


def _display_model_name(model_id: str) -> str:
    if model_id == "combo":
        return "Consenso Geral"
    return model_id.rsplit("/", 1)[-1]


def _model_family(model_id: str) -> str:
    value = model_id.casefold()
    # Order matters: check more-specific tokens before broader ones
    # (e.g. "deepseek" before "qwen", since deepseek model names include "qwen")
    for family in (
        "deepseek", "openai",
        "gemma", "qwen",
        "mistral", "ministral",
        "phi", "microsoft",
        "glm", "llama",
        "nemotron", "nvidia",
        "granite", "ibm",
        "ernie", "baidu",
        "olmo", "allenai",
        "seed", "bytedance",
        "rnj", "essentialai",
        "lfm", "liquid",
    ):
        if family in value:
            return "mistral" if family == "ministral" else family
    if model_id == "combo":
        return "combo"
    return "local"


def _model_image(model_id: str, family: str) -> str:
    if model_id == "combo":
        return ""
    return MODEL_IMAGES.get(family, "")


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    main()
