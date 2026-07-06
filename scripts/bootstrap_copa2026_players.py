"""Dataset de jogadores da Copa 2026 com ratings estilo EA FC e estatísticas do torneio.

Ratings baseados no EA Sports FC 25 (referência pública). Copa stats derivadas
dos resultados reais do torneio. Fonte dos nomes: domínio público / seleções nacionais.
"""

from __future__ import annotations

import json
from pathlib import Path

# fmt: off
# team_id, name, position, age, overall, pace, shoot, pass_, drib, defend, phys, copa_g, copa_a, copa_m
PLAYERS: list[tuple] = [
    # ── NORWAY (T-NOR) ────────────────────────────────────────────────────────
    ("T-NOR","Erling Haaland",        "ST",  25, 94, 89, 97, 66, 80, 45, 88, 4, 1, 5),
    ("T-NOR","Martin Ødegaard",       "CAM", 27, 88, 81, 81, 89, 89, 59, 72, 1, 3, 5),
    ("T-NOR","Alexander Sørloth",     "ST",  29, 82, 76, 83, 71, 73, 46, 84, 2, 1, 5),
    ("T-NOR","Sander Berge",          "CM",  26, 82, 74, 73, 82, 80, 78, 82, 0, 2, 5),
    ("T-NOR","Ørjan Nyland",          "GK",  34, 80, 55, 15, 72, 72, 80, 75, 0, 0, 5),
    # ── ENGLAND (T-ENG) ───────────────────────────────────────────────────────
    ("T-ENG","Jude Bellingham",       "CAM", 21, 91, 83, 85, 90, 91, 73, 83, 3, 2, 5),
    ("T-ENG","Harry Kane",            "ST",  31, 88, 71, 91, 86, 85, 47, 85, 3, 1, 5),
    ("T-ENG","Bukayo Saka",           "RW",  23, 88, 88, 81, 85, 88, 65, 73, 2, 2, 5),
    ("T-ENG","Phil Foden",            "CM",  25, 88, 83, 83, 88, 88, 66, 72, 1, 1, 5),
    ("T-ENG","Trent Alexander-Arnold","RB",  26, 87, 81, 76, 90, 83, 73, 74, 0, 2, 5),
    ("T-ENG","Jordan Pickford",       "GK",  32, 84, 56, 18, 73, 70, 83, 73, 0, 0, 5),
    # ── FRANCE (T-FRA) ────────────────────────────────────────────────────────
    ("T-FRA","Kylian Mbappé",         "ST",  26, 91, 97, 93, 82, 93, 45, 78, 4, 2, 6),
    ("T-FRA","Antoine Griezmann",     "CF",  35, 85, 79, 87, 88, 85, 62, 74, 2, 2, 6),
    ("T-FRA","Eduardo Camavinga",     "CM",  22, 85, 84, 74, 85, 86, 80, 82, 0, 1, 6),
    ("T-FRA","Mike Maignan",          "GK",  29, 88, 56, 17, 74, 70, 87, 79, 0, 0, 6),
    ("T-FRA","Theo Hernandez",        "LB",  27, 84, 87, 71, 79, 82, 75, 83, 1, 1, 6),
    # ── MOROCCO (T-MAR) ───────────────────────────────────────────────────────
    ("T-MAR","Achraf Hakimi",         "RB",  26, 84, 92, 74, 81, 84, 77, 79, 1, 3, 5),
    ("T-MAR","Youssef En-Nesyri",     "ST",  27, 82, 79, 83, 63, 75, 42, 83, 3, 1, 5),
    ("T-MAR","Hakim Ziyech",          "RW",  32, 81, 76, 79, 84, 83, 45, 71, 1, 2, 5),
    ("T-MAR","Sofyan Amrabat",        "CM",  28, 81, 77, 67, 81, 79, 84, 83, 0, 1, 5),
    ("T-MAR","Yassine Bounou (Bono)", "GK",  34, 84, 56, 16, 71, 68, 84, 73, 0, 0, 5),
    # ── PORTUGAL (T-POR) ──────────────────────────────────────────────────────
    ("T-POR","Cristiano Ronaldo",     "ST",  41, 86, 81, 92, 80, 85, 34, 76, 3, 1, 4),
    ("T-POR","Bruno Fernandes",       "CAM", 30, 88, 78, 85, 90, 88, 63, 76, 2, 3, 4),
    ("T-POR","Rúben Dias",            "CB",  28, 88, 72, 39, 74, 74, 91, 85, 0, 0, 4),
    ("T-POR","Bernardo Silva",        "CM",  30, 87, 81, 78, 89, 88, 68, 75, 1, 2, 4),
    ("T-POR","Diogo Costa",           "GK",  26, 85, 57, 17, 74, 72, 85, 74, 0, 0, 4),
    # ── SPAIN (T-ESP) ─────────────────────────────────────────────────────────
    ("T-ESP","Lamine Yamal",          "RW",  18, 90, 91, 84, 87, 93, 42, 69, 3, 3, 4),
    ("T-ESP","Rodri",                 "CDM", 29, 91, 70, 74, 91, 86, 88, 82, 0, 2, 4),
    ("T-ESP","Pedri",                 "CM",  23, 88, 82, 79, 89, 89, 72, 72, 1, 2, 4),
    ("T-ESP","Nico Williams",         "LW",  23, 87, 93, 80, 83, 89, 50, 73, 2, 2, 4),
    ("T-ESP","Marc-André ter Stegen", "GK",  33, 87, 58, 17, 76, 73, 87, 74, 0, 0, 4),
    # ── USA (T-USA) ───────────────────────────────────────────────────────────
    ("T-USA","Christian Pulisic",     "CAM", 26, 84, 84, 80, 83, 84, 57, 74, 2, 2, 4),
    ("T-USA","Tyler Adams",           "CDM", 26, 82, 79, 67, 82, 78, 82, 82, 0, 1, 4),
    ("T-USA","Weston McKennie",       "CM",  27, 80, 77, 74, 79, 77, 77, 83, 1, 0, 4),
    ("T-USA","Gio Reyna",             "CAM", 23, 80, 82, 76, 82, 82, 55, 70, 1, 1, 4),
    ("T-USA","Matt Turner",           "GK",  31, 79, 57, 16, 70, 67, 79, 76, 0, 0, 4),
    # ── BELGIUM (T-BEL) ───────────────────────────────────────────────────────
    ("T-BEL","Kevin De Bruyne",       "CM",  33, 90, 76, 87, 94, 88, 64, 77, 2, 4, 5),
    ("T-BEL","Romelu Lukaku",         "ST",  31, 85, 80, 89, 74, 80, 36, 89, 3, 1, 5),
    ("T-BEL","Thibaut Courtois",      "GK",  33, 89, 56, 18, 75, 73, 89, 82, 0, 0, 5),
    ("T-BEL","Youri Tielemans",       "CM",  28, 83, 74, 79, 85, 82, 73, 75, 1, 2, 5),
    ("T-BEL","Axel Witsel",           "CDM", 36, 79, 63, 64, 79, 77, 80, 80, 0, 0, 5),
    # ── ARGENTINA (T-ARG) ─────────────────────────────────────────────────────
    ("T-ARG","Lionel Messi",          "RW",  38, 90, 82, 88, 92, 94, 34, 65, 3, 4, 4),
    ("T-ARG","Julián Álvarez",        "ST",  25, 86, 83, 86, 81, 85, 53, 79, 2, 1, 4),
    ("T-ARG","Alexis Mac Allister",   "CM",  26, 86, 78, 78, 86, 83, 79, 79, 0, 2, 4),
    ("T-ARG","Rodrigo De Paul",       "CM",  30, 85, 79, 77, 86, 82, 74, 80, 0, 1, 4),
    ("T-ARG","Emiliano Martínez",     "GK",  32, 89, 56, 18, 73, 70, 88, 79, 0, 0, 4),
    # ── EGYPT (T-EGY) ─────────────────────────────────────────────────────────
    ("T-EGY","Mohamed Salah",         "RW",  33, 89, 90, 89, 82, 87, 45, 76, 3, 2, 4),
    ("T-EGY","Trezeguet",             "LW",  30, 79, 82, 74, 73, 77, 46, 74, 1, 1, 4),
    ("T-EGY","Ahmed Hegazi",          "CB",  34, 79, 64, 37, 67, 70, 83, 83, 0, 0, 4),
    ("T-EGY","Mohamed Elneny",        "CM",  32, 78, 72, 66, 79, 74, 76, 74, 0, 1, 4),
    ("T-EGY","El-Shenawy",            "GK",  38, 77, 55, 16, 68, 65, 77, 72, 0, 0, 4),
    # ── SWITZERLAND (T-SUI) ───────────────────────────────────────────────────
    ("T-SUI","Granit Xhaka",          "CM",  32, 84, 69, 74, 86, 81, 82, 79, 0, 2, 4),
    ("T-SUI","Xherdan Shaqiri",       "RW",  33, 79, 80, 76, 79, 78, 47, 73, 1, 2, 4),
    ("T-SUI","Manuel Akanji",         "CB",  29, 84, 78, 43, 75, 74, 88, 83, 0, 0, 4),
    ("T-SUI","Ruben Vargas",          "LW",  26, 79, 84, 73, 79, 79, 55, 72, 1, 1, 4),
    ("T-SUI","Gregor Kobel",          "GK",  27, 83, 57, 17, 73, 72, 83, 74, 0, 0, 4),
    # ── COLOMBIA (T-COL) ──────────────────────────────────────────────────────
    ("T-COL","James Rodríguez",       "CAM", 34, 83, 72, 82, 91, 84, 43, 69, 1, 3, 4),
    ("T-COL","Luis Díaz",             "LW",  28, 85, 90, 79, 80, 85, 50, 75, 2, 2, 4),
    ("T-COL","Jhon Durán",            "ST",  21, 82, 83, 83, 70, 78, 47, 84, 1, 0, 4),
    ("T-COL","Davinson Sánchez",      "CB",  28, 82, 79, 44, 72, 72, 87, 84, 0, 0, 4),
    ("T-COL","David Ospina",          "GK",  36, 80, 55, 17, 71, 68, 80, 73, 0, 0, 4),
    # ── BRAZIL (T-BRA) — eliminado nas oitavas ────────────────────────────────
    ("T-BRA","Vinícius Jr.",          "LW",  24, 91, 96, 83, 77, 92, 49, 75, 2, 2, 4),
    ("T-BRA","Rodrygo",               "RW",  24, 87, 88, 83, 83, 88, 54, 73, 1, 1, 4),
    ("T-BRA","Endrick",               "ST",  19, 83, 86, 84, 72, 82, 46, 78, 1, 0, 4),
    ("T-BRA","Marquinhos",            "CB",  30, 88, 74, 46, 79, 78, 90, 79, 0, 0, 4),
    ("T-BRA","Alisson",               "GK",  32, 89, 57, 17, 78, 75, 89, 79, 0, 0, 4),
    # ── MEXICO (T-MEX) — eliminado nas oitavas ────────────────────────────────
    ("T-MEX","Santiago Giménez",      "ST",  24, 82, 82, 83, 70, 78, 44, 80, 3, 0, 4),
    ("T-MEX","Hirving Lozano",        "RW",  30, 81, 88, 76, 78, 82, 44, 74, 1, 2, 4),
    ("T-MEX","Edson Álvarez",         "CDM", 27, 81, 75, 64, 79, 76, 84, 83, 0, 1, 4),
    ("T-MEX","Guillermo Ochoa",       "GK",  39, 80, 56, 17, 70, 67, 80, 74, 0, 0, 4),
    ("T-MEX","Alexis Vega",           "CAM", 27, 79, 82, 75, 80, 80, 52, 73, 1, 1, 4),
    # ── CANADA (T-CAN) — eliminado ────────────────────────────────────────────
    ("T-CAN","Alphonso Davies",       "LB",  24, 84, 97, 63, 76, 83, 76, 77, 0, 2, 4),
    ("T-CAN","Jonathan David",        "ST",  25, 83, 81, 84, 72, 78, 44, 78, 2, 1, 4),
    ("T-CAN","Cyle Larin",            "ST",  30, 78, 80, 79, 68, 74, 43, 80, 1, 0, 4),
    ("T-CAN","Steven Vitória",        "CB",  37, 78, 67, 44, 71, 70, 83, 81, 0, 0, 4),
    ("T-CAN","Milan Borjan",          "GK",  37, 78, 55, 16, 69, 66, 78, 74, 0, 0, 4),
    # ── GERMANY (T-GER) — eliminado ───────────────────────────────────────────
    ("T-GER","Jamal Musiala",         "CAM", 22, 89, 87, 84, 88, 90, 67, 72, 4, 2, 4),
    ("T-GER","Florian Wirtz",         "CAM", 22, 88, 84, 82, 88, 89, 63, 72, 2, 3, 4),
    ("T-GER","Kai Havertz",           "CF",  26, 85, 82, 82, 83, 82, 64, 80, 3, 1, 4),
    ("T-GER","Manuel Neuer",          "GK",  39, 85, 57, 18, 78, 74, 85, 76, 0, 0, 4),
    ("T-GER","Joshua Kimmich",        "CDM", 30, 87, 76, 76, 90, 85, 85, 76, 0, 2, 4),
]
# fmt: on


def build_json() -> list[dict]:
    records = []
    for row in PLAYERS:
        (team_id, name, pos, age, ovr, pac, sho, pas, dri, def_, phy,
         copa_g, copa_a, copa_m) = row
        records.append({
            "player_id": f"P-{name.split()[0][:3].upper()}{name.split()[-1][:3].upper()}{age}",
            "name": name,
            "team_id": team_id,
            "position": pos,
            "age": age,
            "overall": ovr,
            "pace": pac,
            "shooting": sho,
            "passing": pas,
            "dribbling": dri,
            "defending": def_,
            "physical": phy,
            "copa_goals": copa_g,
            "copa_assists": copa_a,
            "copa_matches": copa_m,
            "source": "ea_fc25_community",
            "snapshot_id": "copa2026-07-06",
        })
    return records


def main() -> None:
    import sys
    sys.path.insert(0, "src")
    out = Path("data/samples/copa2026_players.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    records = build_json()
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gerado: {out} ({len(records)} jogadores)")


if __name__ == "__main__":
    main()
