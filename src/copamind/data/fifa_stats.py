"""Leitores leves para os CSVs oficiais extraidos da FIFA."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from copamind.data.connectors.flags import TEAMS

ROOT = Path("data/fifa")
TEAM_STATS_DIR = ROOT / "team_statistics"
PLAYER_STATS_DIR = ROOT / "player_statistics"

TEAM_TABS = {
    "attack": "ataque.csv",
    "distribution": "distribuicao.csv",
    "defense": "defesa.csv",
    "discipline": "disciplina.csv",
    "goalkeeping": "goleiro.csv",
    "movement": "movimentacao.csv",
    "physical": "fisico.csv",
}

PLAYER_TABS = {
    "scorers": "o_artilheiro.csv",
    "attack": "ataque.csv",
    "distribution": "distribuicao.csv",
    "defense": "defesa.csv",
    "discipline": "disciplina.csv",
    "goalkeeping": "goleiro.csv",
    "movement": "movimentacao.csv",
    "physical": "fisico.csv",
}


def fifa_code(team_id: str) -> str:
    """Retorna o codigo FIFA de uma selecao local."""
    return TEAMS.get(team_id, {}).get("fifa_code", team_id.replace("T-", ""))


def team_label(team_id: str) -> str:
    """Nome exibivel da selecao."""
    team = TEAMS.get(team_id, {})
    return str(team.get("name_pt") or team.get("name_en") or team_id)


def flag_url(team_id: str) -> str:
    """URL publica da bandeira quadrada servida pela FIFA."""
    return f"https://api.fifa.com/api/v3/picture/flags-sq-3/{fifa_code(team_id)}"


@lru_cache(maxsize=64)
def team_rows(tab: str) -> tuple[dict[str, str], ...]:
    """Linhas de uma aba de estatisticas de equipes."""
    return tuple(_read_csv(TEAM_STATS_DIR / TEAM_TABS[tab]))


@lru_cache(maxsize=64)
def player_rows(tab: str) -> tuple[dict[str, str], ...]:
    """Linhas de uma aba de estatisticas de jogadores."""
    return tuple(_read_csv(PLAYER_STATS_DIR / PLAYER_TABS[tab]))


def team_row(team_id: str, tab: str) -> dict[str, str] | None:
    """Busca uma linha de estatisticas de equipe pelo mapeamento local."""
    names = _team_names(team_id)
    for row in team_rows(tab):
        if _norm(row.get("team_name_en")) in names or _norm(row.get("team_name_pt")) in names:
            return row
    return None


def team_summary(team_id: str) -> dict[str, Any]:
    """Resumo compacto para prompt e tela de partida."""
    attack = team_row(team_id, "attack") or {}
    distribution = team_row(team_id, "distribution") or {}
    defense = team_row(team_id, "defense") or {}
    physical = team_row(team_id, "physical") or {}
    goalkeeping = team_row(team_id, "goalkeeping") or {}
    return {
        "team_id": team_id,
        "team_name": team_label(team_id),
        "fifa_code": fifa_code(team_id),
        "flag_url": flag_url(team_id),
        "goals": _num(attack.get("goals")),
        "assists": _num(attack.get("assists")),
        "shots": _num(attack.get("attempt_at_goal")),
        "shots_on_target": _num(attack.get("attempt_at_goal_on_target")),
        "xg": _num(attack.get("xg")),
        "possession": _num(attack.get("possession")),
        "passes": _num(distribution.get("passes")),
        "passing_accuracy": _num(distribution.get("passing_accuracy_rate")),
        "goals_conceded": _num(defense.get("goals_conceded"))
        or _num(goalkeeping.get("goals_conceded")),
        "forced_turnovers": _num(defense.get("forced_turnovers")),
        "clean_sheets": _num(goalkeeping.get("clean_sheets")),
        "saves": _num(goalkeeping.get("goalkeeper_saves")),
        "avg_speed": _num(physical.get("avg_speed")),
        "sprints": _num(physical.get("sprints")),
        "total_distance": _num(physical.get("total_distance")),
    }


def top_players(team_id: str, *, limit: int = 6) -> list[dict[str, Any]]:
    """Principais jogadores de uma selecao com dados oficiais FIFA."""
    code = fifa_code(team_id)
    rows = [row for row in player_rows("scorers") if row.get("team_abbreviation") == code]
    if not rows:
        rows = [row for row in player_rows("attack") if row.get("team_abbreviation") == code]
    rows.sort(
        key=lambda row: (
            _num(row.get("goals")),
            _num(row.get("assists")),
            _num(row.get("attempt_at_goal_on_target")),
            _num(row.get("total_competition_minutes_played")),
        ),
        reverse=True,
    )
    return [_player_card(row) for row in rows[:limit]]


def player_metric_leaders(tab: str, metric: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Ranking de jogadores por metrica numerica."""
    rows = [row for row in player_rows(tab) if row.get(metric) not in {"", None}]
    rows.sort(key=lambda row: _num(row.get(metric)), reverse=True)
    return [_player_card(row) | {"metric_value": _num(row.get(metric))} for row in rows[:limit]]


def available_summary() -> dict[str, int]:
    """Resumo de disponibilidade dos CSVs oficiais."""
    return {
        "team_tabs": sum((TEAM_STATS_DIR / filename).exists() for filename in TEAM_TABS.values()),
        "player_tabs": sum(
            (PLAYER_STATS_DIR / filename).exists() for filename in PLAYER_TABS.values()
        ),
        "team_rows": len(team_rows("attack")) if (TEAM_STATS_DIR / "ataque.csv").exists() else 0,
        "player_rows": len(player_rows("attack"))
        if (PLAYER_STATS_DIR / "ataque.csv").exists()
        else 0,
    }


def clear_fifa_stats_cache() -> None:
    """Limpa caches de leitura para refletir CSVs recem-atualizados."""
    team_rows.cache_clear()
    player_rows.cache_clear()


def _player_card(row: dict[str, str]) -> dict[str, Any]:
    return {
        "player_id": row.get("player_id"),
        "name": row.get("player_name_pt") or row.get("player_name_en"),
        "team": row.get("team_name_pt") or row.get("team_name_en"),
        "team_code": row.get("team_abbreviation"),
        "position": row.get("position_pt") or row.get("position_code"),
        "image_url": row.get("player_image_url"),
        "flag_url": row.get("team_flag_url"),
        "goals": _num(row.get("goals")),
        "assists": _num(row.get("assists")),
        "minutes": _num(row.get("total_competition_minutes_played")),
        "shots_on_target": _num(row.get("attempt_at_goal_on_target")),
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def _team_names(team_id: str) -> set[str]:
    team = TEAMS.get(team_id, {})
    return {_norm(team_id), _norm(team.get("name_pt")), _norm(team.get("name_en"))}


def _norm(value: object) -> str:
    return str(value or "").strip().casefold()


def _num(value: object) -> float:
    if value in {None, ""}:
        return 0.0
    text = str(value).replace("%", "").replace("x", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0
