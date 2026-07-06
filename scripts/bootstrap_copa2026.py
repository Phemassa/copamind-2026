"""Gera data/samples/worldcup2026_copa.json com os resultados reais da Copa 2026.

Dados coletados em 06/07/2026. Partidas pendentes têm score omitido (scheduled).
Execute com: python scripts/bootstrap_copa2026.py
"""

from __future__ import annotations

import json
from pathlib import Path


def T(code):
    return {
    "name": code.split("-")[1] if "-" in code else code,
    "code": code.replace("T-", ""),
}


def t(code: str) -> dict:
    from copamind.data.connectors.flags import TEAMS

    tid = f"T-{code}"
    info = TEAMS.get(tid, {})
    return {"name": info.get("name_pt", code), "code": code}


ROUNDS: list[dict] = [
    # ──────────────────── FASE DE GRUPOS ────────────────────
    {
        "name": "Grupo A - Rodada 1",
        "matches": [
            {
                "num": 1,
                "date": "2026-06-11",
                "group": "Group A",
                "team1": t("MEX"),
                "team2": t("RSA"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 2,
                "date": "2026-06-11",
                "group": "Group A",
                "team1": t("KOR"),
                "team2": t("CZE"),
                "score1": 2,
                "score2": 1,
            },
        ],
    },
    {
        "name": "Grupo B/D - Rodada 1",
        "matches": [
            {
                "num": 3,
                "date": "2026-06-12",
                "group": "Group B",
                "team1": t("CAN"),
                "team2": t("BIH"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 4,
                "date": "2026-06-12",
                "group": "Group D",
                "team1": t("USA"),
                "team2": t("PAR"),
                "score1": 4,
                "score2": 1,
            },
        ],
    },
    {
        "name": "Grupo B/C - Rodada 1",
        "matches": [
            {
                "num": 5,
                "date": "2026-06-13",
                "group": "Group B",
                "team1": t("QAT"),
                "team2": t("SUI"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 6,
                "date": "2026-06-13",
                "group": "Group C",
                "team1": t("BRA"),
                "team2": t("MAR"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 7,
                "date": "2026-06-13",
                "group": "Group C",
                "team1": t("HAI"),
                "team2": t("SCO"),
                "score1": 0,
                "score2": 1,
            },
        ],
    },
    {
        "name": "Grupo D/E/F - Rodada 1",
        "matches": [
            {
                "num": 8,
                "date": "2026-06-14",
                "group": "Group D",
                "team1": t("AUS"),
                "team2": t("TUR"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 9,
                "date": "2026-06-14",
                "group": "Group E",
                "team1": t("GER"),
                "team2": t("CUW"),
                "score1": 7,
                "score2": 1,
            },
            {
                "num": 10,
                "date": "2026-06-14",
                "group": "Group F",
                "team1": t("NED"),
                "team2": t("JPN"),
                "score1": 2,
                "score2": 2,
            },
            {
                "num": 11,
                "date": "2026-06-14",
                "group": "Group E",
                "team1": t("CIV"),
                "team2": t("ECU"),
                "score1": 1,
                "score2": 0,
            },
            {
                "num": 12,
                "date": "2026-06-14",
                "group": "Group F",
                "team1": t("SWE"),
                "team2": t("TUN"),
                "score1": 5,
                "score2": 1,
            },
        ],
    },
    {
        "name": "Grupo G/H - Rodada 1",
        "matches": [
            {
                "num": 13,
                "date": "2026-06-15",
                "group": "Group H",
                "team1": t("ESP"),
                "team2": t("CPV"),
                "score1": 0,
                "score2": 0,
            },
            {
                "num": 14,
                "date": "2026-06-15",
                "group": "Group G",
                "team1": t("BEL"),
                "team2": t("EGY"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 15,
                "date": "2026-06-15",
                "group": "Group H",
                "team1": t("KSA"),
                "team2": t("URU"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 16,
                "date": "2026-06-15",
                "group": "Group G",
                "team1": t("IRN"),
                "team2": t("NZL"),
                "score1": 2,
                "score2": 2,
            },
        ],
    },
    {
        "name": "Grupo I/J - Rodada 1",
        "matches": [
            {
                "num": 17,
                "date": "2026-06-16",
                "group": "Group I",
                "team1": t("FRA"),
                "team2": t("SEN"),
                "score1": 3,
                "score2": 1,
            },
            {
                "num": 18,
                "date": "2026-06-16",
                "group": "Group I",
                "team1": t("IRQ"),
                "team2": t("NOR"),
                "score1": 1,
                "score2": 4,
            },
            {
                "num": 19,
                "date": "2026-06-16",
                "group": "Group J",
                "team1": t("ARG"),
                "team2": t("ALG"),
                "score1": 3,
                "score2": 0,
            },
        ],
    },
    {
        "name": "Grupo J/K/L - Rodada 1",
        "matches": [
            {
                "num": 20,
                "date": "2026-06-17",
                "group": "Group J",
                "team1": t("AUT"),
                "team2": t("JOR"),
                "score1": 3,
                "score2": 1,
            },
            {
                "num": 21,
                "date": "2026-06-17",
                "group": "Group K",
                "team1": t("POR"),
                "team2": t("COD"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 22,
                "date": "2026-06-17",
                "group": "Group L",
                "team1": t("ENG"),
                "team2": t("CRO"),
                "score1": 4,
                "score2": 2,
            },
            {
                "num": 23,
                "date": "2026-06-17",
                "group": "Group L",
                "team1": t("GHA"),
                "team2": t("PAN"),
                "score1": 1,
                "score2": 0,
            },
            {
                "num": 24,
                "date": "2026-06-17",
                "group": "Group K",
                "team1": t("UZB"),
                "team2": t("COL"),
                "score1": 1,
                "score2": 3,
            },
        ],
    },
    # Rodada 2
    {
        "name": "Grupo A/B - Rodada 2",
        "matches": [
            {
                "num": 25,
                "date": "2026-06-18",
                "group": "Group A",
                "team1": t("CZE"),
                "team2": t("RSA"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 26,
                "date": "2026-06-18",
                "group": "Group B",
                "team1": t("SUI"),
                "team2": t("BIH"),
                "score1": 4,
                "score2": 1,
            },
            {
                "num": 27,
                "date": "2026-06-18",
                "group": "Group B",
                "team1": t("CAN"),
                "team2": t("QAT"),
                "score1": 6,
                "score2": 0,
            },
            {
                "num": 28,
                "date": "2026-06-18",
                "group": "Group A",
                "team1": t("MEX"),
                "team2": t("KOR"),
                "score1": 1,
                "score2": 0,
            },
        ],
    },
    {
        "name": "Grupo C/D - Rodada 2",
        "matches": [
            {
                "num": 29,
                "date": "2026-06-19",
                "group": "Group D",
                "team1": t("USA"),
                "team2": t("AUS"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 30,
                "date": "2026-06-19",
                "group": "Group C",
                "team1": t("SCO"),
                "team2": t("MAR"),
                "score1": 0,
                "score2": 1,
            },
            {
                "num": 31,
                "date": "2026-06-19",
                "group": "Group C",
                "team1": t("BRA"),
                "team2": t("HAI"),
                "score1": 3,
                "score2": 0,
            },
            {
                "num": 32,
                "date": "2026-06-19",
                "group": "Group D",
                "team1": t("TUR"),
                "team2": t("PAR"),
                "score1": 0,
                "score2": 1,
            },
        ],
    },
    {
        "name": "Grupo E/F - Rodada 2",
        "matches": [
            {
                "num": 33,
                "date": "2026-06-20",
                "group": "Group F",
                "team1": t("NED"),
                "team2": t("SWE"),
                "score1": 5,
                "score2": 1,
            },
            {
                "num": 34,
                "date": "2026-06-20",
                "group": "Group E",
                "team1": t("GER"),
                "team2": t("CIV"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 35,
                "date": "2026-06-20",
                "group": "Group E",
                "team1": t("ECU"),
                "team2": t("CUW"),
                "score1": 0,
                "score2": 0,
            },
        ],
    },
    {
        "name": "Grupo F/G/H - Rodada 2",
        "matches": [
            {
                "num": 36,
                "date": "2026-06-21",
                "group": "Group F",
                "team1": t("TUN"),
                "team2": t("JPN"),
                "score1": 0,
                "score2": 4,
            },
            {
                "num": 37,
                "date": "2026-06-21",
                "group": "Group H",
                "team1": t("ESP"),
                "team2": t("KSA"),
                "score1": 4,
                "score2": 0,
            },
            {
                "num": 38,
                "date": "2026-06-21",
                "group": "Group G",
                "team1": t("BEL"),
                "team2": t("IRN"),
                "score1": 0,
                "score2": 0,
            },
            {
                "num": 39,
                "date": "2026-06-21",
                "group": "Group H",
                "team1": t("URU"),
                "team2": t("CPV"),
                "score1": 2,
                "score2": 2,
            },
            {
                "num": 40,
                "date": "2026-06-21",
                "group": "Group G",
                "team1": t("NZL"),
                "team2": t("EGY"),
                "score1": 1,
                "score2": 3,
            },
        ],
    },
    {
        "name": "Grupo I/J - Rodada 2",
        "matches": [
            {
                "num": 41,
                "date": "2026-06-22",
                "group": "Group J",
                "team1": t("ARG"),
                "team2": t("AUT"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 42,
                "date": "2026-06-22",
                "group": "Group I",
                "team1": t("FRA"),
                "team2": t("IRQ"),
                "score1": 3,
                "score2": 0,
            },
            {
                "num": 43,
                "date": "2026-06-22",
                "group": "Group I",
                "team1": t("NOR"),
                "team2": t("SEN"),
                "score1": 3,
                "score2": 2,
            },
            {
                "num": 44,
                "date": "2026-06-22",
                "group": "Group J",
                "team1": t("JOR"),
                "team2": t("ALG"),
                "score1": 1,
                "score2": 2,
            },
        ],
    },
    {
        "name": "Grupo K/L - Rodada 2",
        "matches": [
            {
                "num": 45,
                "date": "2026-06-23",
                "group": "Group K",
                "team1": t("POR"),
                "team2": t("UZB"),
                "score1": 5,
                "score2": 0,
            },
            {
                "num": 46,
                "date": "2026-06-23",
                "group": "Group L",
                "team1": t("ENG"),
                "team2": t("GHA"),
                "score1": 0,
                "score2": 0,
            },
            {
                "num": 47,
                "date": "2026-06-23",
                "group": "Group L",
                "team1": t("PAN"),
                "team2": t("CRO"),
                "score1": 0,
                "score2": 1,
            },
            {
                "num": 48,
                "date": "2026-06-23",
                "group": "Group K",
                "team1": t("COL"),
                "team2": t("COD"),
                "score1": 1,
                "score2": 0,
            },
        ],
    },
    # Rodada 3
    {
        "name": "Grupo A/B/C - Rodada 3",
        "matches": [
            {
                "num": 49,
                "date": "2026-06-24",
                "group": "Group B",
                "team1": t("SUI"),
                "team2": t("CAN"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 50,
                "date": "2026-06-24",
                "group": "Group B",
                "team1": t("BIH"),
                "team2": t("QAT"),
                "score1": 3,
                "score2": 1,
            },
            {
                "num": 51,
                "date": "2026-06-24",
                "group": "Group C",
                "team1": t("MAR"),
                "team2": t("HAI"),
                "score1": 4,
                "score2": 2,
            },
            {
                "num": 52,
                "date": "2026-06-24",
                "group": "Group C",
                "team1": t("SCO"),
                "team2": t("BRA"),
                "score1": 0,
                "score2": 3,
            },
            {
                "num": 53,
                "date": "2026-06-24",
                "group": "Group A",
                "team1": t("RSA"),
                "team2": t("KOR"),
                "score1": 1,
                "score2": 0,
            },
            {
                "num": 54,
                "date": "2026-06-24",
                "group": "Group A",
                "team1": t("CZE"),
                "team2": t("MEX"),
                "score1": 0,
                "score2": 3,
            },
        ],
    },
    {
        "name": "Grupo D/E/F - Rodada 3",
        "matches": [
            {
                "num": 55,
                "date": "2026-06-25",
                "group": "Group E",
                "team1": t("CUW"),
                "team2": t("CIV"),
                "score1": 0,
                "score2": 2,
            },
            {
                "num": 56,
                "date": "2026-06-25",
                "group": "Group E",
                "team1": t("ECU"),
                "team2": t("GER"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 57,
                "date": "2026-06-25",
                "group": "Group F",
                "team1": t("TUN"),
                "team2": t("NED"),
                "score1": 1,
                "score2": 3,
            },
            {
                "num": 58,
                "date": "2026-06-25",
                "group": "Group F",
                "team1": t("JPN"),
                "team2": t("SWE"),
                "score1": 1,
                "score2": 1,
            },
            {
                "num": 59,
                "date": "2026-06-25",
                "group": "Group D",
                "team1": t("TUR"),
                "team2": t("USA"),
                "score1": 3,
                "score2": 2,
            },
            {
                "num": 60,
                "date": "2026-06-25",
                "group": "Group D",
                "team1": t("PAR"),
                "team2": t("AUS"),
                "score1": 0,
                "score2": 0,
            },
        ],
    },
    {
        "name": "Grupo G/H/I - Rodada 3",
        "matches": [
            {
                "num": 61,
                "date": "2026-06-26",
                "group": "Group I",
                "team1": t("NOR"),
                "team2": t("FRA"),
                "score1": 1,
                "score2": 4,
            },
            {
                "num": 62,
                "date": "2026-06-26",
                "group": "Group I",
                "team1": t("SEN"),
                "team2": t("IRQ"),
                "score1": 5,
                "score2": 0,
            },
            {
                "num": 63,
                "date": "2026-06-26",
                "group": "Group H",
                "team1": t("CPV"),
                "team2": t("KSA"),
                "score1": 0,
                "score2": 0,
            },
            {
                "num": 64,
                "date": "2026-06-26",
                "group": "Group H",
                "team1": t("URU"),
                "team2": t("ESP"),
                "score1": 0,
                "score2": 1,
            },
            {
                "num": 65,
                "date": "2026-06-26",
                "group": "Group G",
                "team1": t("NZL"),
                "team2": t("BEL"),
                "score1": 1,
                "score2": 5,
            },
            {
                "num": 66,
                "date": "2026-06-26",
                "group": "Group G",
                "team1": t("EGY"),
                "team2": t("IRN"),
                "score1": 1,
                "score2": 1,
            },
        ],
    },
    {
        "name": "Grupo J/K/L - Rodada 3",
        "matches": [
            {
                "num": 67,
                "date": "2026-06-27",
                "group": "Group L",
                "team1": t("PAN"),
                "team2": t("ENG"),
                "score1": 0,
                "score2": 2,
            },
            {
                "num": 68,
                "date": "2026-06-27",
                "group": "Group L",
                "team1": t("CRO"),
                "team2": t("GHA"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 69,
                "date": "2026-06-27",
                "group": "Group K",
                "team1": t("COL"),
                "team2": t("POR"),
                "score1": 0,
                "score2": 0,
            },
            {
                "num": 70,
                "date": "2026-06-27",
                "group": "Group K",
                "team1": t("COD"),
                "team2": t("UZB"),
                "score1": 3,
                "score2": 1,
            },
            {
                "num": 71,
                "date": "2026-06-27",
                "group": "Group J",
                "team1": t("ALG"),
                "team2": t("AUT"),
                "score1": 3,
                "score2": 3,
            },
            {
                "num": 72,
                "date": "2026-06-27",
                "group": "Group J",
                "team1": t("JOR"),
                "team2": t("ARG"),
                "score1": 1,
                "score2": 3,
            },
        ],
    },
    # ──────────────────── SEGUNDA RODADA (R32) ────────────────────
    {
        "name": "Segunda rodada (Round of 32)",
        "matches": [
            {
                "num": 73,
                "date": "2026-06-28",
                "team1": t("RSA"),
                "team2": t("CAN"),
                "score1": 0,
                "score2": 1,
            },
            {
                "num": 74,
                "date": "2026-06-29",
                "team1": t("BRA"),
                "team2": t("JPN"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 75,
                "date": "2026-06-29",
                "team1": t("GER"),
                "team2": t("PAR"),
                "score": {"ft": [1, 1], "p": [3, 4]},
            },  # PAR wins pens
            {
                "num": 76,
                "date": "2026-06-29",
                "team1": t("NED"),
                "team2": t("MAR"),
                "score": {"ft": [1, 1], "p": [2, 3]},
            },  # MAR wins pens
            {
                "num": 77,
                "date": "2026-06-30",
                "team1": t("CIV"),
                "team2": t("NOR"),
                "score1": 1,
                "score2": 2,
            },
            {
                "num": 78,
                "date": "2026-06-30",
                "team1": t("FRA"),
                "team2": t("SWE"),
                "score1": 3,
                "score2": 0,
            },
            {
                "num": 79,
                "date": "2026-06-30",
                "team1": t("MEX"),
                "team2": t("ECU"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 80,
                "date": "2026-07-01",
                "team1": t("ENG"),
                "team2": t("COD"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 81,
                "date": "2026-07-01",
                "team1": t("BEL"),
                "team2": t("SEN"),
                "score1": 3,
                "score2": 2,
            },  # AET
            {
                "num": 82,
                "date": "2026-07-01",
                "team1": t("USA"),
                "team2": t("BIH"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 83,
                "date": "2026-07-02",
                "team1": t("ESP"),
                "team2": t("AUT"),
                "score1": 3,
                "score2": 0,
            },
            {
                "num": 84,
                "date": "2026-07-02",
                "team1": t("POR"),
                "team2": t("CRO"),
                "score1": 2,
                "score2": 1,
            },
            {
                "num": 85,
                "date": "2026-07-02",
                "team1": t("SUI"),
                "team2": t("ALG"),
                "score1": 2,
                "score2": 0,
            },
            {
                "num": 86,
                "date": "2026-07-03",
                "team1": t("AUS"),
                "team2": t("EGY"),
                "score": {"ft": [1, 1], "p": [2, 4]},
            },  # EGY wins pens
            {
                "num": 87,
                "date": "2026-07-03",
                "team1": t("ARG"),
                "team2": t("CPV"),
                "score1": 3,
                "score2": 2,
            },  # AET
            {
                "num": 88,
                "date": "2026-07-03",
                "team1": t("COL"),
                "team2": t("GHA"),
                "score1": 1,
                "score2": 0,
            },
        ],
    },
    # ──────────────────── OITAVAS DE FINAL (R16) ────────────────────
    {
        "name": "Oitavas de final (Round of 16)",
        "matches": [
            {
                "num": 89,
                "date": "2026-07-04",
                "team1": t("CAN"),
                "team2": t("MAR"),
                "score1": 0,
                "score2": 3,
            },
            {
                "num": 90,
                "date": "2026-07-04",
                "team1": t("PAR"),
                "team2": t("FRA"),
                "score1": 0,
                "score2": 1,
            },
            {
                "num": 91,
                "date": "2026-07-05",
                "team1": t("BRA"),
                "team2": t("NOR"),
                "score1": 1,
                "score2": 2,
            },
            {
                "num": 92,
                "date": "2026-07-05",
                "team1": t("MEX"),
                "team2": t("ENG"),
                "score1": 2,
                "score2": 3,
            },
            {"num": 93, "date": "2026-07-06", "team1": t("POR"), "team2": t("ESP")},  # hoje 15:00
            {"num": 94, "date": "2026-07-06", "team1": t("USA"), "team2": t("BEL")},  # hoje 20:00
            {"num": 95, "date": "2026-07-07", "team1": t("ARG"), "team2": t("EGY")},  # amanhã 12:00
            {"num": 96, "date": "2026-07-07", "team1": t("SUI"), "team2": t("COL")},  # amanhã 16:00
        ],
    },
    # ──────────────────── QUARTAS DE FINAL ────────────────────
    {
        "name": "Quartas de final",
        "matches": [
            {"num": 97, "date": "2026-07-09", "team1": t("FRA"), "team2": t("MAR")},  # FRA vs MAR
            {
                "num": 98,
                "date": "2026-07-10",
                "team1": {"name": "A definir", "code": "TBD"},
                "team2": {"name": "A definir", "code": "TBD2"},
            },
            {"num": 99, "date": "2026-07-11", "team1": t("NOR"), "team2": t("ENG")},  # NOR vs ENG
            {
                "num": 100,
                "date": "2026-07-11",
                "team1": {"name": "A definir", "code": "TBD3"},
                "team2": {"name": "A definir", "code": "TBD4"},
            },
        ],
    },
    # ──────────────────── SEMIFINAIS ────────────────────
    {
        "name": "Semifinais",
        "matches": [
            {
                "num": 101,
                "date": "2026-07-14",
                "team1": {"name": "A definir", "code": "TBD5"},
                "team2": {"name": "A definir", "code": "TBD6"},
            },
            {
                "num": 102,
                "date": "2026-07-15",
                "team1": {"name": "A definir", "code": "TBD7"},
                "team2": {"name": "A definir", "code": "TBD8"},
            },
        ],
    },
    # ──────────────────── FINAL ────────────────────
    {
        "name": "Final",
        "matches": [
            {
                "num": 103,
                "date": "2026-07-18",
                "team1": {"name": "A definir", "code": "TBD9"},
                "team2": {"name": "A definir", "code": "TBD10"},
            },  # 3rd place
            {
                "num": 104,
                "date": "2026-07-19",
                "team1": {"name": "A definir", "code": "TBD11"},
                "team2": {"name": "A definir", "code": "TBD12"},
            },
        ],
    },
]


def main() -> None:
    import sys

    sys.path.insert(0, "src")
    out = {"name": "Copa do Mundo 2026", "rounds": ROUNDS}
    path = Path("data/samples/worldcup2026_copa.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    matches = sum(len(r["matches"]) for r in ROUNDS)
    print(f"Gerado: {path} ({matches} partidas)")


if __name__ == "__main__":
    main()
