"""Internacionalização da interface (EN / PT-BR) — DECISIONS ADR-0006.

Apenas a camada de apresentação é traduzida. Dados factuais e de linhagem
(ids, códigos FIFA, snapshots) permanecem canônicos e não são traduzidos.
"""

from __future__ import annotations

DEFAULT_LOCALE = "pt-BR"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt-BR": {
        "app_title": "CopaMind 2026",
        "subtitle": "Inteligência esportiva local para a Copa 2026",
        "language": "Idioma",
        "disclaimer": (
            "As probabilidades são experimentais e educacionais. Dependem da "
            "qualidade e atualidade dos dados e não garantem resultado."
        ),
        "nav_home": "Visão geral",
        "nav_ranking": "Chances de título",
        "nav_team": "Análise de seleção",
        "nav_predict": "Previsão de partida",
        "section_status": "Estado da base",
        "teams": "Seleções",
        "matches": "Partidas",
        "snapshot": "Snapshot",
        "predictions": "Previsões",
        "no_data": "Nenhum dado encontrado.",
        "run_ingest_hint": "Rode `copamind ingest sample` para carregar o exemplo.",
        "championship_chances": "Chances de título",
        "qualify": "Classificação",
        "title": "Título",
        "iterations": "Simulações",
        "team_analysis": "Análise de seleção",
        "select_team": "Selecione a seleção",
        "elo_rating": "Rating Elo",
        "recent_form": "Forma recente",
        "window": "Janela",
        "points": "Pontos",
        "wins": "V",
        "draws": "E",
        "losses": "D",
        "goals_for": "GP",
        "goals_against": "GC",
        "ppg": "Pts/jogo",
        "last_matches": "Últimas partidas",
        "match_prediction": "Previsão de partida",
        "home": "Mandante",
        "away": "Visitante",
        "neutral": "Campo neutro",
        "predict_button": "Prever",
        "home_win": "Vitória mandante",
        "draw": "Empate",
        "away_win": "Vitória visitante",
        "expected_goals": "Gols esperados",
        "most_likely_score": "Placar mais provável",
        "over25": "Mais de 2,5 gols",
        "same_team_error": "Escolha seleções diferentes.",
    },
    "en": {
        "app_title": "CopaMind 2026",
        "subtitle": "Local sports intelligence for the 2026 World Cup",
        "language": "Language",
        "disclaimer": (
            "Probabilities are experimental and educational. They depend on data "
            "quality and freshness and do not guarantee any outcome."
        ),
        "nav_home": "Overview",
        "nav_ranking": "Title chances",
        "nav_team": "Team analysis",
        "nav_predict": "Match prediction",
        "section_status": "Database status",
        "teams": "Teams",
        "matches": "Matches",
        "snapshot": "Snapshot",
        "predictions": "Predictions",
        "no_data": "No data found.",
        "run_ingest_hint": "Run `copamind ingest sample` to load the sample.",
        "championship_chances": "Title chances",
        "qualify": "Qualify",
        "title": "Title",
        "iterations": "Simulations",
        "team_analysis": "Team analysis",
        "select_team": "Select the team",
        "elo_rating": "Elo rating",
        "recent_form": "Recent form",
        "window": "Window",
        "points": "Points",
        "wins": "W",
        "draws": "D",
        "losses": "L",
        "goals_for": "GF",
        "goals_against": "GA",
        "ppg": "Pts/game",
        "last_matches": "Last matches",
        "match_prediction": "Match prediction",
        "home": "Home",
        "away": "Away",
        "neutral": "Neutral venue",
        "predict_button": "Predict",
        "home_win": "Home win",
        "draw": "Draw",
        "away_win": "Away win",
        "expected_goals": "Expected goals",
        "most_likely_score": "Most likely score",
        "over25": "Over 2.5 goals",
        "same_team_error": "Choose different teams.",
    },
}


def available_locales() -> list[str]:
    """Retorna os idiomas disponíveis (PT-BR primeiro)."""
    return list(TRANSLATIONS)


class Translator:
    """Tradutor simples baseado em dicionário, com fallback para PT-BR e a chave."""

    def __init__(self, locale: str = DEFAULT_LOCALE) -> None:
        self.locale = locale if locale in TRANSLATIONS else DEFAULT_LOCALE

    def t(self, key: str) -> str:
        """Traduz uma chave; cai para PT-BR e, por fim, para a própria chave."""
        return TRANSLATIONS[self.locale].get(key) or TRANSLATIONS[DEFAULT_LOCALE].get(key) or key
