"""Cards em Markdown (PT-BR e EN) para LinkedIn (MASTER_PLAN §30).

Gera cartões a partir das saídas dos modelos. Cada card sai nos dois idiomas
para dobrar o alcance, sempre com o disclaimer educacional.
"""

from __future__ import annotations

from copamind.data.repositories import DuckDBRepository
from copamind.models.ensemble.service import ensemble_match
from copamind.simulation.service import build_default_config, run_simulation
from copamind.ui.i18n import Translator, available_locales


def championship_card(repo: DuckDBRepository, *, iterations: int = 5000) -> dict[str, str]:
    """Card com as chances de título por seleção, em cada idioma."""
    config = build_default_config(repo, iterations=iterations)
    result = run_simulation(repo, config)
    teams = {t.team_id: t for t in repo.list_teams()}

    cards: dict[str, str] = {}
    for locale in available_locales():
        tr = Translator(locale)
        lines = [
            f"# 🏆 CopaMind 2026 — {tr.t('championship_chances')}",
            "",
            f"| {tr.t('teams')} | {tr.t('qualify')} | {tr.t('title')} |",
            "| --- | ---: | ---: |",
        ]
        for team in result.teams:
            name = teams[team.team_id].name if team.team_id in teams else team.team_id
            lines.append(
                f"| {name} | {team.qualified_probability:.1%} | {team.champion_probability:.1%} |"
            )
        lines.extend(
            [
                "",
                f"_{result.iterations} {tr.t('iterations')} (Monte Carlo)._",
                "",
                f"> {tr.t('disclaimer')}",
            ]
        )
        cards[locale] = "\n".join(lines)
    return cards


def matchup_card(
    repo: DuckDBRepository, home_id: str, away_id: str, *, neutral_venue: bool = True
) -> dict[str, str]:
    """Card de confronto com probabilidades do ensemble, em cada idioma."""
    prediction = ensemble_match(repo, home_id, away_id, neutral_venue=neutral_venue)
    teams = {t.team_id: t for t in repo.list_teams()}
    home_name = teams[home_id].name if home_id in teams else home_id
    away_name = teams[away_id].name if away_id in teams else away_id

    cards: dict[str, str] = {}
    for locale in available_locales():
        tr = Translator(locale)
        cards[locale] = "\n".join(
            [
                f"# ⚽ {home_name} x {away_name}",
                "",
                f"- {tr.t('home_win')}: **{prediction.prob_home:.1%}**",
                f"- {tr.t('draw')}: **{prediction.prob_draw:.1%}**",
                f"- {tr.t('away_win')}: **{prediction.prob_away:.1%}**",
                "",
                f"> {tr.t('disclaimer')}",
            ]
        )
    return cards
