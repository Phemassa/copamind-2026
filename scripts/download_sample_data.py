"""Gera um dataset sintético, fictício e redistribuível para testes e demo.

Não usa dados reais (MASTER_PLAN §1.6). Determinístico por seed. Escreve
``data/samples/teams.json`` e ``data/samples/matches.json``.

Uso:
    python scripts/download_sample_data.py
"""

from __future__ import annotations

import itertools
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

SEED = 2026
SNAPSHOT_ID = "sample-2026-07-06"
COLLECTED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OUTPUT_DIR = Path("data/samples")

# Seleções fictícias (não representam países reais).
TEAMS = [
    {"team_id": "T-NTL", "name": "Nortlândia", "fifa_code": "NTL", "confederation": "UEFA"},
    {"team_id": "T-SDR", "name": "Sudria", "fifa_code": "SDR", "confederation": "CONMEBOL"},
    {"team_id": "T-EST", "name": "Estland", "fifa_code": "EST", "confederation": "AFC"},
    {"team_id": "T-WST", "name": "Westória", "fifa_code": "WST", "confederation": "CAF"},
]


def build_teams() -> list[dict[str, object]]:
    """Constrói a lista de seleções com linhagem."""
    teams: list[dict[str, object]] = []
    for rank, team in enumerate(TEAMS, start=1):
        teams.append(
            {
                **team,
                "country": team["name"],
                "fifa_ranking": rank,
                "elo_rating": 1500.0 + (len(TEAMS) - rank) * 25.0,
                "active": True,
                "source": "synthetic",
                "collected_at": COLLECTED_AT.isoformat(),
                "available_at": COLLECTED_AT.isoformat(),
                "snapshot_id": SNAPSHOT_ID,
            }
        )
    return teams


def build_matches() -> list[dict[str, object]]:
    """Constrói 20 partidas finalizadas únicas (turno e returno com datas distintas)."""
    rng = random.Random(SEED)
    matches: list[dict[str, object]] = []
    base_date = datetime(2025, 6, 1, 18, 0, tzinfo=UTC)
    pairings = list(itertools.permutations([t["team_id"] for t in TEAMS], 2))
    # 12 confrontos únicos + 8 confrontos extras em novas datas => 20 partidas únicas.
    schedule = pairings + pairings[:8]
    for index, (home, away) in enumerate(schedule):
        match_date = base_date + timedelta(days=index * 7)
        home_score = rng.randint(0, 4)
        away_score = rng.randint(0, 3)
        matches.append(
            {
                "match_id": f"M-{index:03d}",
                "competition": "Amistosos Internacionais (fictício)",
                "stage": "friendly",
                "match_date": match_date.isoformat(),
                "home_team_id": home,
                "away_team_id": away,
                "neutral_venue": False,
                "home_score": home_score,
                "away_score": away_score,
                "status": "finished",
                "importance_weight": 1.0,
                "source": "synthetic",
                "collected_at": COLLECTED_AT.isoformat(),
                # Dados disponíveis no dia seguinte à partida (anti-leakage).
                "available_at": (match_date + timedelta(days=1)).isoformat(),
                "snapshot_id": SNAPSHOT_ID,
            }
        )
    return matches


def main() -> None:
    """Gera e grava os arquivos de amostra."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    teams = build_teams()
    matches = build_matches()
    # Inclui 2 duplicatas exatas para exercitar a deduplicação na ingestão.
    matches_with_dupes = [*matches, matches[0], matches[1]]
    (OUTPUT_DIR / "teams.json").write_text(
        json.dumps(teams, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "matches.json").write_text(
        json.dumps(matches_with_dupes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Gerados {len(teams)} times e {len(matches)} partidas únicas "
        f"({len(matches_with_dupes)} registros com duplicatas) em {OUTPUT_DIR}/"
    )


if __name__ == "__main__":
    main()
