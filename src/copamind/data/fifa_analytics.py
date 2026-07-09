"""Analytics derivados dos CSVs FIFA para contexto enxuto das LLMs."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from statistics import mean
from typing import Any

from copamind.data.fifa_stats import fifa_code, player_rows, team_label, team_row, team_rows

SEMANTIC_CATALOG: dict[str, dict[str, str]] = {
    "attack": {
        "goals": "producao ofensiva realizada",
        "xg": "qualidade das chances criadas",
        "attempt_at_goal": "volume de finalizacoes",
        "attempt_at_goal_on_target": "volume de finalizacoes certas",
        "attempt_at_goal_conversion_rate": "eficiencia de conversao",
    },
    "distribution": {
        "passes": "circulacao e controle",
        "passing_accuracy_rate": "precisao da circulacao",
        "linebreaks_attempted_defensive_line": "tentativa de romper linha defensiva",
        "linebreak_attempted_defensive_line_rate": "eficiencia de ruptura",
    },
    "defense": {
        "goals_conceded": "vulnerabilidade defensiva",
        "forced_turnovers": "recuperacao forcada",
        "ball_recovery_time": "tempo para recuperar a bola",
        "defensive_pressures_applied": "pressao defensiva total",
    },
    "discipline": {
        "fouls_against": "faltas cometidas",
        "yellow_cards": "risco de suspensao/controle emocional",
        "red_cards": "risco de expulsao",
        "offsides": "risco de desperdicio por impedimento",
    },
    "goalkeeping": {
        "clean_sheets": "jogos sem sofrer gol",
        "goals_conceded": "gols sofridos",
        "goalkeeper_saves": "defesas do goleiro",
        "goalkeeper_defensive_actions_inside_penalty_area": "intervencoes na area",
    },
    "movement": {
        "offers_to_receive_total": "ofertas para receber",
        "offers_to_receive_in_behind": "ataque a profundidade",
        "receptions_in_behind": "recebimentos em profundidade",
        "receptions_between_midfield_and_defensive_line": "recebimentos entre linhas",
        "receptions_under_pressure": "participacao sob pressao",
    },
    "physical": {
        "avg_speed": "velocidade media",
        "speed_runs": "corridas de alta intensidade",
        "sprints": "sprints",
        "total_distance": "carga total percorrida",
    },
}

TEAM_INDEXES: dict[str, tuple[tuple[str, str, bool, float], ...]] = {
    "attack_index": (
        ("attack", "xg", True, 0.30),
        ("attack", "attempt_at_goal_on_target", True, 0.25),
        ("attack", "goals", True, 0.25),
        ("attack", "attempt_at_goal", True, 0.20),
    ),
    "chance_quality_index": (
        ("attack", "xg", True, 0.45),
        ("attack", "attempt_at_goal_on_target", True, 0.30),
        ("attack", "attempt_at_goal_inside_the_penalty_area", True, 0.25),
    ),
    "finishing_index": (
        ("attack", "attempt_at_goal_conversion_rate", True, 0.45),
        ("attack", "xg_goal_effiency_rate", True, 0.30),
        ("attack", "goals", True, 0.25),
    ),
    "defense_index": (
        ("defense", "goals_conceded", False, 0.35),
        ("goalkeeping", "clean_sheets", True, 0.25),
        ("defense", "forced_turnovers", True, 0.20),
        ("defense", "ball_recovery_time", False, 0.20),
    ),
    "keeper_index": (
        ("goalkeeping", "clean_sheets", True, 0.35),
        ("goalkeeping", "goals_conceded", False, 0.30),
        ("goalkeeping", "goalkeeper_saves", True, 0.20),
        ("goalkeeping", "goalkeeper_defensive_actions_inside_penalty_area", True, 0.15),
    ),
    "control_index": (
        ("distribution", "passes", True, 0.30),
        ("distribution", "passing_accuracy_rate", True, 0.30),
        ("attack", "possession", True, 0.20),
        ("distribution", "attempted_switches_of_play", True, 0.20),
    ),
    "pressing_index": (
        ("defense", "forced_turnovers", True, 0.35),
        ("defense", "defensive_pressures_applied", True, 0.30),
        ("defense", "direct_defensive_pressures_applied", True, 0.20),
        ("defense", "ball_recovery_time", False, 0.15),
    ),
    "transition_index": (
        ("movement", "offers_to_receive_in_behind", True, 0.25),
        ("movement", "receptions_in_behind", True, 0.30),
        ("movement", "receptions_between_midfield_and_defensive_line", True, 0.25),
        ("distribution", "linebreaks_attempted_defensive_line", True, 0.20),
    ),
    "discipline_risk": (
        ("discipline", "yellow_cards", True, 0.35),
        ("discipline", "red_cards", True, 0.30),
        ("discipline", "fouls_against", True, 0.25),
        ("discipline", "indirect_red_cards", True, 0.10),
    ),
    "physical_load": (
        ("physical", "total_distance", True, 0.35),
        ("physical", "sprints", True, 0.30),
        ("physical", "speed_runs", True, 0.25),
        ("physical", "avg_speed", True, 0.10),
    ),
}

PER90_CAPS = {
    "goals": 3.0,
    "assists": 3.0,
    "attempt_at_goal_on_target": 8.0,
    "xg": 3.0,
    "linebreaks_attempted_defensive_line": 30.0,
    "receptions_in_behind": 15.0,
    "defensive_pressures_applied": 80.0,
    "yellow_cards": 2.0,
    "red_cards": 1.0,
    "goalkeeper_saves": 8.0,
}


@dataclass(frozen=True)
class PlayerRole:
    role: str
    score: float
    reason: str


def team_analytics(team_id: str) -> dict[str, Any]:
    """Pacote analitico enxuto de uma equipe para prompt e snapshots."""
    raw = _team_metrics(team_id)
    indexes = {
        name: round(_weighted_percentile(parts, raw), 3)
        for name, parts in TEAM_INDEXES.items()
    }
    indexes["volatility_index"] = round(_volatility_index(raw, indexes), 3)
    indexes["champion_profile_score"] = round(_champion_profile_score(indexes), 3)
    return {
        "team_id": team_id,
        "team_name": team_label(team_id),
        "fifa_code": fifa_code(team_id),
        "indexes": indexes,
        "core_metrics": _core_metrics(raw),
        "evidence": _team_evidence(team_id, raw, indexes),
        "quality": _team_quality(raw),
    }


def matchup_analytics(home_team_id: str, away_team_id: str) -> dict[str, Any]:
    """Compara duas selecoes e calcula deltas/sinais de imprevisibilidade."""
    home = team_analytics(home_team_id)
    away = team_analytics(away_team_id)
    deltas = {
        key: round(float(home["indexes"].get(key, 0.0)) - float(away["indexes"].get(key, 0.0)), 3)
        for key in sorted(set(home["indexes"]) | set(away["indexes"]))
    }
    upset_risk = _upset_risk_score(home["indexes"], away["indexes"], deltas)
    return {
        "schema_version": "copamind.fifa_analytics.v2",
        "home": home,
        "away": away,
        "deltas": deltas,
        "upset_risk_score": round(upset_risk, 3),
        "summary": _matchup_summary(home, away, deltas, upset_risk),
        "top_evidence": _matchup_evidence(home, away, deltas, upset_risk),
    }


def key_players_analytics(team_id: str, *, limit: int = 8) -> list[dict[str, Any]]:
    """Jogadores-chave unificando abas FIFA por papel e confiabilidade."""
    players = _team_players(team_id)
    cards: list[dict[str, Any]] = []
    for player in players.values():
        role = _best_player_role(player)
        if role.score <= 0:
            continue
        minutes = _num(player.get("total_competition_minutes_played"))
        sample = "unknown_minutes" if minutes <= 0 else "small" if minutes < 90 else "normal"
        confidence = _player_confidence(player, role.score)
        cards.append(
            {
                "player_id": player.get("player_id"),
                "name": player.get("player_name_pt") or player.get("player_name_en"),
                "team": (
                    player.get("team_name_pt")
                    or player.get("team_name_en")
                    or team_label(team_id)
                ),
                "team_code": player.get("team_abbreviation") or fifa_code(team_id),
                "position": player.get("position_pt") or player.get("position_code"),
                "image_url": player.get("player_image_url"),
                "flag_url": player.get("team_flag_url"),
                "role": role.role,
                "role_score": round(role.score, 3),
                "reason": role.reason,
                "confidence": round(confidence, 3),
                "sample": sample,
                "minutes": minutes,
                "per90": _player_per90(player),
            }
        )
    cards.sort(
        key=lambda item: (item["confidence"], item["role_score"], item["minutes"]),
        reverse=True,
    )
    return cards[:limit]


def _team_metrics(team_id: str) -> dict[tuple[str, str], float]:
    raw: dict[tuple[str, str], float] = {}
    for tab in (
        "attack",
        "distribution",
        "defense",
        "discipline",
        "goalkeeping",
        "movement",
        "physical",
    ):
        row = team_row(team_id, tab) or {}
        for key, value in row.items():
            if key.startswith("rank_") or key in {
                "team_external_id",
                "team_name_pt",
                "team_name_en",
            }:
                continue
            raw[(tab, key)] = _num(value)
    return raw


def _core_metrics(raw: dict[tuple[str, str], float]) -> dict[str, float]:
    fields = {
        "goals": ("attack", "goals"),
        "xg": ("attack", "xg"),
        "shots": ("attack", "attempt_at_goal"),
        "shots_on_target": ("attack", "attempt_at_goal_on_target"),
        "conversion_rate": ("attack", "attempt_at_goal_conversion_rate"),
        "possession": ("attack", "possession"),
        "passes": ("distribution", "passes"),
        "passing_accuracy": ("distribution", "passing_accuracy_rate"),
        "goals_conceded": ("defense", "goals_conceded"),
        "clean_sheets": ("goalkeeping", "clean_sheets"),
        "saves": ("goalkeeping", "goalkeeper_saves"),
        "forced_turnovers": ("defense", "forced_turnovers"),
        "yellow_cards": ("discipline", "yellow_cards"),
        "red_cards": ("discipline", "red_cards"),
        "sprints": ("physical", "sprints"),
        "total_distance": ("physical", "total_distance"),
    }
    return {name: raw.get(key, 0.0) for name, key in fields.items()}


def _weighted_percentile(
    parts: tuple[tuple[str, str, bool, float], ...],
    raw: dict[tuple[str, str], float],
) -> float:
    values = []
    weights = []
    for tab, metric, higher_is_better, weight in parts:
        value = raw.get((tab, metric))
        if value is None:
            continue
        values.append(_percentile(tab, metric, value, higher_is_better=higher_is_better))
        weights.append(weight)
    if not values:
        return 0.0
    total_weight = sum(weights)
    weighted_sum = sum(
        value * weight for value, weight in zip(values, weights, strict=False)
    )
    return weighted_sum / total_weight


@lru_cache(maxsize=256)
def _metric_distribution(tab: str, metric: str) -> tuple[float, ...]:
    values = [_num(row.get(metric)) for row in team_rows(tab) if row.get(metric) not in {"", None}]
    return tuple(sorted(values))


def _percentile(tab: str, metric: str, value: float, *, higher_is_better: bool) -> float:
    values = _metric_distribution(tab, metric)
    if not values:
        return 0.0
    lower_or_equal = sum(1 for item in values if item <= value)
    pct = lower_or_equal / len(values)
    if not higher_is_better:
        pct = 1 - pct + (1 / len(values))
    return max(0.0, min(1.0, pct))


def _volatility_index(raw: dict[tuple[str, str], float], indexes: dict[str, float]) -> float:
    xg = raw.get(("attack", "xg"), 0.0)
    goals = raw.get(("attack", "goals"), 0.0)
    overperformance = min(abs(goals - xg) / max(xg, 1.0), 1.0)
    cards = indexes.get("discipline_risk", 0.0)
    keeper_exposure = max(
        0.0,
        indexes.get("keeper_index", 0.0) - indexes.get("defense_index", 0.0),
    )
    finishing_gap = abs(
        indexes.get("finishing_index", 0.0) - indexes.get("chance_quality_index", 0.0)
    )
    return mean([overperformance, cards, keeper_exposure, finishing_gap])


def _champion_profile_score(indexes: dict[str, float]) -> float:
    score = (
        indexes.get("defense_index", 0.0) * 0.22
        + indexes.get("keeper_index", 0.0) * 0.12
        + indexes.get("chance_quality_index", 0.0) * 0.18
        + indexes.get("attack_index", 0.0) * 0.14
        + indexes.get("finishing_index", 0.0) * 0.10
        + indexes.get("control_index", 0.0) * 0.10
        + indexes.get("transition_index", 0.0) * 0.08
        + (1 - indexes.get("discipline_risk", 0.0)) * 0.06
    )
    return max(0.0, min(1.0, score))


def _upset_risk_score(
    home_indexes: dict[str, float],
    away_indexes: dict[str, float],
    deltas: dict[str, float],
) -> float:
    champion_gap = abs(deltas.get("champion_profile_score", 0.0))
    tight_match = 1 - min(champion_gap / 0.35, 1.0)
    volatility = mean(
        [
            home_indexes.get("volatility_index", 0.0),
            away_indexes.get("volatility_index", 0.0),
        ]
    )
    defense_attack_cross = 1 - min(
        abs(deltas.get("attack_index", 0.0) + deltas.get("defense_index", 0.0)) / 0.8,
        1.0,
    )
    penaltyish = mean(
        [
            home_indexes.get("keeper_index", 0.0),
            away_indexes.get("keeper_index", 0.0),
            1 - abs(deltas.get("defense_index", 0.0)),
        ]
    )
    return max(0.0, min(1.0, mean([tight_match, volatility, defense_attack_cross, penaltyish])))


def _team_evidence(
    team_id: str,
    raw: dict[tuple[str, str], float],
    indexes: dict[str, float],
) -> list[dict[str, Any]]:
    team = team_label(team_id)
    metrics = _core_metrics(raw)
    candidates = [
        (
            "attack",
            indexes["attack_index"],
            f"{team}: ataque em percentil {indexes['attack_index']:.2f}.",
        ),
        (
            "chance_quality",
            indexes["chance_quality_index"],
            f"{team}: xG {metrics['xg']:.2f} e {metrics['shots_on_target']:.0f} chutes no alvo.",
        ),
        (
            "defense",
            indexes["defense_index"],
            (
                f"{team}: {metrics['goals_conceded']:.0f} gols sofridos e "
                f"{metrics['clean_sheets']:.0f} clean sheets."
            ),
        ),
        (
            "control",
            indexes["control_index"],
            (
                f"{team}: {metrics['passes']:.0f} passes, "
                f"{metrics['passing_accuracy']:.0f}% de acerto."
            ),
        ),
        (
            "discipline",
            indexes["discipline_risk"],
            (
                f"{team}: risco disciplinar com {metrics['yellow_cards']:.0f} amarelos "
                f"e {metrics['red_cards']:.0f} vermelhos."
            ),
        ),
    ]
    candidates.sort(key=lambda item: item[1], reverse=True)
    return [
        {
            "id": f"{team_id}.team.{name}",
            "type": "team_analytics",
            "strength": round(score, 3),
            "text": text,
        }
        for name, score, text in candidates[:4]
    ]


def _team_quality(raw: dict[tuple[str, str], float]) -> dict[str, Any]:
    present = sum(1 for value in raw.values() if value != 0)
    return {
        "non_zero_metrics": present,
        "confidence": "high" if present >= 30 else "medium" if present >= 15 else "low",
    }


def _matchup_summary(
    home: dict[str, Any],
    away: dict[str, Any],
    deltas: dict[str, float],
    upset_risk: float,
) -> str:
    leader = home if deltas.get("champion_profile_score", 0.0) >= 0 else away
    risk = "alto" if upset_risk >= 0.66 else "medio" if upset_risk >= 0.4 else "baixo"
    return (
        f"{leader['team_name']} tem melhor perfil composto, mas o risco de zebra e {risk}. "
        f"Deltas principais: ataque {deltas.get('attack_index', 0):+.2f}, "
        f"defesa {deltas.get('defense_index', 0):+.2f}, "
        f"controle {deltas.get('control_index', 0):+.2f}."
    )


def _matchup_evidence(
    home: dict[str, Any],
    away: dict[str, Any],
    deltas: dict[str, float],
    upset_risk: float,
) -> list[dict[str, Any]]:
    ranked = sorted(deltas.items(), key=lambda item: abs(item[1]), reverse=True)
    evidence = [
        {
            "id": f"matchup.delta.{name}",
            "type": "matchup_delta",
            "strength": round(abs(value), 3),
            "text": f"Delta {name}: {home['team_name']} {value:+.3f} vs {away['team_name']}.",
        }
        for name, value in ranked[:5]
    ]
    evidence.append(
        {
            "id": "matchup.upset_risk",
            "type": "uncertainty",
            "strength": round(upset_risk, 3),
            "text": f"Risco de imprevisibilidade/zebra: {upset_risk:.3f}.",
        }
    )
    return evidence


def _team_players(team_id: str) -> dict[str, dict[str, Any]]:
    code = fifa_code(team_id)
    players: dict[str, dict[str, Any]] = {}
    tabs = (
        "scorers",
        "attack",
        "distribution",
        "defense",
        "discipline",
        "goalkeeping",
        "movement",
        "physical",
    )
    for tab in tabs:
        for row in player_rows(tab):
            if row.get("team_abbreviation") != code:
                continue
            player_id = str(row.get("player_id") or "")
            if not player_id:
                continue
            merged = players.setdefault(player_id, {})
            for key, value in row.items():
                if value not in {"", None}:
                    merged[key] = value
    return players


def _best_player_role(player: dict[str, Any]) -> PlayerRole:
    goals_p90 = _per90(player, "goals")
    assists_p90 = _per90(player, "assists")
    shots_on_p90 = _per90(player, "attempt_at_goal_on_target")
    xg_p90 = _per90(player, "xg")
    linebreak_p90 = _per90(player, "linebreaks_attempted_defensive_line")
    behind_p90 = _per90(player, "receptions_in_behind")
    pressure_p90 = _per90(player, "defensive_pressures_applied")
    cards_p90 = _per90_sum(player, ("yellow_cards", "red_cards"), weights=(1.0, 2.0))
    saves_p90 = _per90(player, "goalkeeper_saves")
    roles = [
        PlayerRole(
            "finalizador",
            goals_p90 * 0.45 + shots_on_p90 * 0.30 + xg_p90 * 0.25,
            "gols, xG e chutes no alvo",
        ),
        PlayerRole(
            "criador",
            assists_p90 * 0.45 + (linebreak_p90 / 10) * 0.35 + behind_p90 * 0.20,
            "assistencias e rupturas",
        ),
        PlayerRole(
            "ruptura",
            behind_p90 * 0.55 + (linebreak_p90 / 10) * 0.45,
            "profundidade e quebras de linha",
        ),
        PlayerRole("pressao_defensiva", pressure_p90 / 20, "pressao defensiva por 90"),
        PlayerRole("risco_disciplinar", cards_p90, "cartoes por 90"),
        PlayerRole("goleiro_decisivo", saves_p90 / 5, "defesas por 90"),
    ]
    return max(roles, key=lambda item: item.score)


def _player_confidence(player: dict[str, Any], role_score: float) -> float:
    minutes = _num(player.get("total_competition_minutes_played"))
    minute_factor = min(minutes / 180, 1.0) if minutes else 0.10
    data_points = sum(
        1
        for key in (
            "goals",
            "assists",
            "attempt_at_goal_on_target",
            "xg",
            "defensive_pressures_applied",
            "goalkeeper_saves",
            "receptions_in_behind",
        )
        if _num(player.get(key)) > 0
    )
    data_factor = min(data_points / 3, 1.0)
    role_factor = min(role_score / 3, 1.0)
    confidence = minute_factor * 0.55 + data_factor * 0.25 + role_factor * 0.20
    return max(0.05, min(1.0, confidence))


def _player_per90(player: dict[str, Any]) -> dict[str, float]:
    fields = {
        "goals": "goals",
        "assists": "assists",
        "shots_on_target": "attempt_at_goal_on_target",
        "xg": "xg",
        "pressures": "defensive_pressures_applied",
        "receptions_in_behind": "receptions_in_behind",
        "saves": "goalkeeper_saves",
    }
    return {name: round(_per90(player, field), 3) for name, field in fields.items()}


def _per90(player: dict[str, Any], field: str) -> float:
    value = _num(player.get(field))
    minutes = _num(player.get("total_competition_minutes_played"))
    if minutes <= 0:
        return min(value, PER90_CAPS.get(field, value))
    return min(value * 90 / minutes, PER90_CAPS.get(field, value * 90 / minutes))


def _per90_sum(
    player: dict[str, Any],
    fields: tuple[str, ...],
    *,
    weights: tuple[float, ...],
) -> float:
    value = sum(
        _num(player.get(field)) * weight
        for field, weight in zip(fields, weights, strict=True)
    )
    minutes = _num(player.get("total_competition_minutes_played"))
    if minutes <= 0:
        return value
    return value * 90 / minutes


def _num(value: object) -> float:
    if value in {None, ""}:
        return 0.0
    text = str(value).replace("%", "").replace("x", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0
