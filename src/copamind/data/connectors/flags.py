"""Mapeamento de seleções da Copa 2026 para bandeiras e metadados."""

from __future__ import annotations

# code → {emoji, iso2, name_pt, name_en, group, fifa_code}
TEAMS: dict[str, dict[str, str]] = {
    # Grupo A
    "T-MEX": {
        "emoji": "🇲🇽",
        "iso2": "mx",
        "name_pt": "México",
        "name_en": "Mexico",
        "group": "A",
        "fifa_code": "MEX",
    },
    "T-RSA": {
        "emoji": "🇿🇦",
        "iso2": "za",
        "name_pt": "África do Sul",
        "name_en": "South Africa",
        "group": "A",
        "fifa_code": "RSA",
    },
    "T-KOR": {
        "emoji": "🇰🇷",
        "iso2": "kr",
        "name_pt": "Coreia do Sul",
        "name_en": "South Korea",
        "group": "A",
        "fifa_code": "KOR",
    },
    "T-CZE": {
        "emoji": "🇨🇿",
        "iso2": "cz",
        "name_pt": "Tchéquia",
        "name_en": "Czechia",
        "group": "A",
        "fifa_code": "CZE",
    },
    # Grupo B
    "T-CAN": {
        "emoji": "🇨🇦",
        "iso2": "ca",
        "name_pt": "Canadá",
        "name_en": "Canada",
        "group": "B",
        "fifa_code": "CAN",
    },
    "T-BIH": {
        "emoji": "🇧🇦",
        "iso2": "ba",
        "name_pt": "Bósnia e Herzegovina",
        "name_en": "Bosnia & Herzegovina",
        "group": "B",
        "fifa_code": "BIH",
    },
    "T-SUI": {
        "emoji": "🇨🇭",
        "iso2": "ch",
        "name_pt": "Suíça",
        "name_en": "Switzerland",
        "group": "B",
        "fifa_code": "SUI",
    },
    "T-QAT": {
        "emoji": "🇶🇦",
        "iso2": "qa",
        "name_pt": "Catar",
        "name_en": "Qatar",
        "group": "B",
        "fifa_code": "QAT",
    },
    # Grupo C
    "T-BRA": {
        "emoji": "🇧🇷",
        "iso2": "br",
        "name_pt": "Brasil",
        "name_en": "Brazil",
        "group": "C",
        "fifa_code": "BRA",
    },
    "T-MAR": {
        "emoji": "🇲🇦",
        "iso2": "ma",
        "name_pt": "Marrocos",
        "name_en": "Morocco",
        "group": "C",
        "fifa_code": "MAR",
    },
    "T-HAI": {
        "emoji": "🇭🇹",
        "iso2": "ht",
        "name_pt": "Haiti",
        "name_en": "Haiti",
        "group": "C",
        "fifa_code": "HAI",
    },
    "T-SCO": {
        "emoji": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "iso2": "gb-sct",
        "name_pt": "Escócia",
        "name_en": "Scotland",
        "group": "C",
        "fifa_code": "SCO",
    },
    # Grupo D
    "T-USA": {
        "emoji": "🇺🇸",
        "iso2": "us",
        "name_pt": "Estados Unidos",
        "name_en": "USA",
        "group": "D",
        "fifa_code": "USA",
    },
    "T-PAR": {
        "emoji": "🇵🇾",
        "iso2": "py",
        "name_pt": "Paraguai",
        "name_en": "Paraguay",
        "group": "D",
        "fifa_code": "PAR",
    },
    "T-AUS": {
        "emoji": "🇦🇺",
        "iso2": "au",
        "name_pt": "Austrália",
        "name_en": "Australia",
        "group": "D",
        "fifa_code": "AUS",
    },
    "T-TUR": {
        "emoji": "🇹🇷",
        "iso2": "tr",
        "name_pt": "Turquia",
        "name_en": "Turkey",
        "group": "D",
        "fifa_code": "TUR",
    },
    # Grupo E
    "T-GER": {
        "emoji": "🇩🇪",
        "iso2": "de",
        "name_pt": "Alemanha",
        "name_en": "Germany",
        "group": "E",
        "fifa_code": "GER",
    },
    "T-CIV": {
        "emoji": "🇨🇮",
        "iso2": "ci",
        "name_pt": "Costa do Marfim",
        "name_en": "Côte d'Ivoire",
        "group": "E",
        "fifa_code": "CIV",
    },
    "T-ECU": {
        "emoji": "🇪🇨",
        "iso2": "ec",
        "name_pt": "Equador",
        "name_en": "Ecuador",
        "group": "E",
        "fifa_code": "ECU",
    },
    "T-CUW": {
        "emoji": "🇨🇼",
        "iso2": "cw",
        "name_pt": "Curaçao",
        "name_en": "Curaçao",
        "group": "E",
        "fifa_code": "CUW",
    },
    # Grupo F
    "T-NED": {
        "emoji": "🇳🇱",
        "iso2": "nl",
        "name_pt": "Países Baixos",
        "name_en": "Netherlands",
        "group": "F",
        "fifa_code": "NED",
    },
    "T-JPN": {
        "emoji": "🇯🇵",
        "iso2": "jp",
        "name_pt": "Japão",
        "name_en": "Japan",
        "group": "F",
        "fifa_code": "JPN",
    },
    "T-SWE": {
        "emoji": "🇸🇪",
        "iso2": "se",
        "name_pt": "Suécia",
        "name_en": "Sweden",
        "group": "F",
        "fifa_code": "SWE",
    },
    "T-TUN": {
        "emoji": "🇹🇳",
        "iso2": "tn",
        "name_pt": "Tunísia",
        "name_en": "Tunisia",
        "group": "F",
        "fifa_code": "TUN",
    },
    # Grupo G
    "T-BEL": {
        "emoji": "🇧🇪",
        "iso2": "be",
        "name_pt": "Bélgica",
        "name_en": "Belgium",
        "group": "G",
        "fifa_code": "BEL",
    },
    "T-EGY": {
        "emoji": "🇪🇬",
        "iso2": "eg",
        "name_pt": "Egito",
        "name_en": "Egypt",
        "group": "G",
        "fifa_code": "EGY",
    },
    "T-IRN": {
        "emoji": "🇮🇷",
        "iso2": "ir",
        "name_pt": "Irã",
        "name_en": "Iran",
        "group": "G",
        "fifa_code": "IRN",
    },
    "T-NZL": {
        "emoji": "🇳🇿",
        "iso2": "nz",
        "name_pt": "Nova Zelândia",
        "name_en": "New Zealand",
        "group": "G",
        "fifa_code": "NZL",
    },
    # Grupo H
    "T-ESP": {
        "emoji": "🇪🇸",
        "iso2": "es",
        "name_pt": "Espanha",
        "name_en": "Spain",
        "group": "H",
        "fifa_code": "ESP",
    },
    "T-KSA": {
        "emoji": "🇸🇦",
        "iso2": "sa",
        "name_pt": "Arábia Saudita",
        "name_en": "Saudi Arabia",
        "group": "H",
        "fifa_code": "KSA",
    },
    "T-URU": {
        "emoji": "🇺🇾",
        "iso2": "uy",
        "name_pt": "Uruguai",
        "name_en": "Uruguay",
        "group": "H",
        "fifa_code": "URU",
    },
    "T-CPV": {
        "emoji": "🇨🇻",
        "iso2": "cv",
        "name_pt": "Cabo Verde",
        "name_en": "Cape Verde",
        "group": "H",
        "fifa_code": "CPV",
    },
    # Grupo I
    "T-FRA": {
        "emoji": "🇫🇷",
        "iso2": "fr",
        "name_pt": "França",
        "name_en": "France",
        "group": "I",
        "fifa_code": "FRA",
    },
    "T-SEN": {
        "emoji": "🇸🇳",
        "iso2": "sn",
        "name_pt": "Senegal",
        "name_en": "Senegal",
        "group": "I",
        "fifa_code": "SEN",
    },
    "T-IRQ": {
        "emoji": "🇮🇶",
        "iso2": "iq",
        "name_pt": "Iraque",
        "name_en": "Iraq",
        "group": "I",
        "fifa_code": "IRQ",
    },
    "T-NOR": {
        "emoji": "🇳🇴",
        "iso2": "no",
        "name_pt": "Noruega",
        "name_en": "Norway",
        "group": "I",
        "fifa_code": "NOR",
    },
    # Grupo J
    "T-ARG": {
        "emoji": "🇦🇷",
        "iso2": "ar",
        "name_pt": "Argentina",
        "name_en": "Argentina",
        "group": "J",
        "fifa_code": "ARG",
    },
    "T-ALG": {
        "emoji": "🇩🇿",
        "iso2": "dz",
        "name_pt": "Argélia",
        "name_en": "Algeria",
        "group": "J",
        "fifa_code": "ALG",
    },
    "T-AUT": {
        "emoji": "🇦🇹",
        "iso2": "at",
        "name_pt": "Áustria",
        "name_en": "Austria",
        "group": "J",
        "fifa_code": "AUT",
    },
    "T-JOR": {
        "emoji": "🇯🇴",
        "iso2": "jo",
        "name_pt": "Jordânia",
        "name_en": "Jordan",
        "group": "J",
        "fifa_code": "JOR",
    },
    # Grupo K
    "T-POR": {
        "emoji": "🇵🇹",
        "iso2": "pt",
        "name_pt": "Portugal",
        "name_en": "Portugal",
        "group": "K",
        "fifa_code": "POR",
    },
    "T-COD": {
        "emoji": "🇨🇩",
        "iso2": "cd",
        "name_pt": "RD Congo",
        "name_en": "DR Congo",
        "group": "K",
        "fifa_code": "COD",
    },
    "T-UZB": {
        "emoji": "🇺🇿",
        "iso2": "uz",
        "name_pt": "Uzbequistão",
        "name_en": "Uzbekistan",
        "group": "K",
        "fifa_code": "UZB",
    },
    "T-COL": {
        "emoji": "🇨🇴",
        "iso2": "co",
        "name_pt": "Colômbia",
        "name_en": "Colombia",
        "group": "K",
        "fifa_code": "COL",
    },
    # Grupo L
    "T-ENG": {
        "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "iso2": "gb-eng",
        "name_pt": "Inglaterra",
        "name_en": "England",
        "group": "L",
        "fifa_code": "ENG",
    },
    "T-CRO": {
        "emoji": "🇭🇷",
        "iso2": "hr",
        "name_pt": "Croácia",
        "name_en": "Croatia",
        "group": "L",
        "fifa_code": "CRO",
    },
    "T-GHA": {
        "emoji": "🇬🇭",
        "iso2": "gh",
        "name_pt": "Gana",
        "name_en": "Ghana",
        "group": "L",
        "fifa_code": "GHA",
    },
    "T-PAN": {
        "emoji": "🇵🇦",
        "iso2": "pa",
        "name_pt": "Panamá",
        "name_en": "Panama",
        "group": "L",
        "fifa_code": "PAN",
    },
}

# Índice reverso: nome PT/EN → team_id
_NAME_INDEX: dict[str, str] = {}
for _tid, _t in TEAMS.items():
    _NAME_INDEX[_t["name_pt"].lower()] = _tid
    _NAME_INDEX[_t["name_en"].lower()] = _tid
    _NAME_INDEX[_t["fifa_code"].lower()] = _tid


def lookup(name_or_code: str) -> str | None:
    """Retorna o team_id a partir de nome (PT/EN) ou código FIFA."""
    return _NAME_INDEX.get(name_or_code.strip().lower())


def flag_emoji(team_id: str) -> str:
    """Retorna o emoji de bandeira da seleção."""
    return TEAMS.get(team_id, {}).get("emoji", "🏳")


def flag_img_url(team_id: str, width: int = 20) -> str:
    """URL da imagem de bandeira (flagcdn.com)."""
    iso = TEAMS.get(team_id, {}).get("iso2", "")
    if not iso:
        return ""
    return f"https://flagcdn.com/w{width}/{iso}.png"


def display(team_id: str, locale: str = "pt-BR") -> str:
    """Emoji + nome traduzido para exibição."""
    t = TEAMS.get(team_id)
    if t is None:
        return team_id
    name = t["name_pt"] if locale == "pt-BR" else t["name_en"]
    return f"{t['emoji']} {name}"


def group_teams(group: str) -> list[str]:
    """Lista de team_ids de um grupo."""
    return [tid for tid, t in TEAMS.items() if t.get("group") == group]
