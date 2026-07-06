"""Regenera data/samples/teams.json e data/samples/matches.json com dados reais
da Copa 2026, derivados do worldcup2026_copa.json já existente.

Execute: python scripts/generate_copa_samples.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from copamind.data.connectors.openfootball import read_worldcup_file
from copamind.data.schemas import MatchStatus

COPA_JSON  = Path("data/samples/worldcup2026_copa.json")
OUT_TEAMS  = Path("data/samples/teams.json")
OUT_MATCHES = Path("data/samples/matches.json")
SNAPSHOT   = "copa2026-07-06"


def main() -> None:
    if not COPA_JSON.exists():
        print(f"[erro] {COPA_JSON} não encontrado. Execute: python scripts/bootstrap_copa2026.py")
        sys.exit(1)

    teams, matches = read_worldcup_file(COPA_JSON, snapshot_id=SNAPSHOT)

    teams_json = [t.model_dump(mode="json") for t in teams]

    # Apenas partidas com placar registrado (status=finished)
    completed = [m for m in matches if m.status is MatchStatus.finished]
    # Exclui IDs de equipes placeholder ("TBD*")
    completed = [m for m in completed if not m.home_team_id.startswith("T-TBD")
                 and not m.away_team_id.startswith("T-TBD")]

    matches_json = [m.model_dump(mode="json") for m in completed]

    OUT_TEAMS.write_text(json.dumps(teams_json, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MATCHES.write_text(json.dumps(matches_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Gerado: teams.json   → {len(teams_json)} seleções")
    print(f"Gerado: matches.json → {len(matches_json)} partidas concluídas")

    # Mostra um exemplo de time para validação
    if teams_json:
        print("\nExemplo de time:")
        print(json.dumps(teams_json[0], ensure_ascii=False, indent=2))
    if matches_json:
        print("\nExemplo de partida:")
        print(json.dumps(matches_json[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
