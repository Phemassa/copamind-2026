"""Dashboard Streamlit do CopaMind 2026 (bilíngue EN/PT-BR).

Execute com: `copamind ui serve` ou `streamlit run apps/streamlit/app.py`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from copamind.core.config import get_settings
from copamind.data.repositories import DuckDBRepository
from copamind.ui.dashboard import (
    championship_table,
    database_status,
    match_prediction_view,
    team_analysis_view,
)
from copamind.ui.i18n import DEFAULT_LOCALE, Translator, available_locales


@st.cache_resource
def _repo_path() -> str:
    return str(get_settings().duckdb_path)


def _open_repo() -> DuckDBRepository:
    repo = DuckDBRepository(_repo_path())
    repo.create_schema()
    return repo


def main() -> None:
    """Ponto de entrada do dashboard."""
    st.set_page_config(page_title="CopaMind 2026", page_icon="⚽", layout="wide")

    locales = available_locales()
    locale = st.sidebar.selectbox(
        "🌐 Idioma / Language",
        locales,
        index=locales.index(DEFAULT_LOCALE),
    )
    tr = Translator(locale)

    st.title(f"⚽ {tr.t('app_title')}")
    st.caption(tr.t("subtitle"))

    with _open_repo() as repo:
        status = database_status(repo)
        if status["teams"] == 0:
            st.warning(f"{tr.t('no_data')} {tr.t('run_ingest_hint')}")
            st.stop()

        page = st.sidebar.radio(
            tr.t("section_status"),
            [
                tr.t("nav_home"),
                tr.t("nav_ranking"),
                tr.t("nav_team"),
                tr.t("nav_predict"),
            ],
        )

        if page == tr.t("nav_home"):
            _render_home(repo, tr, status)
        elif page == tr.t("nav_ranking"):
            _render_ranking(repo, tr)
        elif page == tr.t("nav_team"):
            _render_team(repo, tr)
        elif page == tr.t("nav_predict"):
            _render_predict(repo, tr)

    st.sidebar.divider()
    st.sidebar.info(tr.t("disclaimer"))


def _render_home(repo: DuckDBRepository, tr: Translator, status: dict) -> None:
    st.subheader(tr.t("section_status"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(tr.t("teams"), status["teams"])
    col2.metric(tr.t("matches"), status["matches"])
    col3.metric(tr.t("predictions"), status["predictions"])
    col4.metric(tr.t("snapshot"), status["snapshot"] or "-")


def _render_ranking(repo: DuckDBRepository, tr: Translator) -> None:
    st.subheader(tr.t("championship_chances"))
    iterations = st.slider(tr.t("iterations"), 1000, 50000, 5000, step=1000)
    rows = championship_table(repo, iterations=iterations)
    frame = pd.DataFrame(rows).set_index("team_id")
    frame.columns = [tr.t("qualify"), tr.t("title")]
    st.bar_chart(frame[tr.t("title")])
    st.dataframe(
        frame.style.format({tr.t("qualify"): "{:.1%}", tr.t("title"): "{:.1%}"}),
        use_container_width=True,
    )


def _render_team(repo: DuckDBRepository, tr: Translator) -> None:
    st.subheader(tr.t("team_analysis"))
    teams = repo.list_teams()
    options = {t.name: t.team_id for t in teams}
    name = st.selectbox(tr.t("select_team"), list(options))
    view = team_analysis_view(repo, options[name])

    st.metric(tr.t("elo_rating"), f"{view['elo_rating']:.0f}")
    st.markdown(f"**{tr.t('recent_form')}**")
    form = pd.DataFrame(view["windows"])
    st.dataframe(form, use_container_width=True)

    st.markdown(f"**{tr.t('last_matches')}**")
    st.dataframe(pd.DataFrame(view["last_matches"]), use_container_width=True)


def _render_predict(repo: DuckDBRepository, tr: Translator) -> None:
    st.subheader(tr.t("match_prediction"))
    teams = repo.list_teams()
    options = {t.name: t.team_id for t in teams}
    names = list(options)
    col1, col2 = st.columns(2)
    home = col1.selectbox(tr.t("home"), names, index=0)
    away = col2.selectbox(tr.t("away"), names, index=min(1, len(names) - 1))
    neutral = st.checkbox(tr.t("neutral"), value=True)

    if st.button(tr.t("predict_button")):
        if options[home] == options[away]:
            st.error(tr.t("same_team_error"))
            return
        pred = match_prediction_view(repo, options[home], options[away], neutral_venue=neutral)
        c1, c2, c3 = st.columns(3)
        c1.metric(tr.t("home_win"), f"{pred['prob_home_win']:.1%}")
        c2.metric(tr.t("draw"), f"{pred['prob_draw']:.1%}")
        c3.metric(tr.t("away_win"), f"{pred['prob_away_win']:.1%}")
        st.write(
            f"{tr.t('expected_goals')}: "
            f"{pred['expected_home_goals']:.2f} x {pred['expected_away_goals']:.2f}"
        )
        score = pred["most_likely_score"]
        st.write(f"{tr.t('most_likely_score')}: {score[0]}-{score[1]}")
        st.write(f"{tr.t('over25')}: {pred['prob_over_2_5']:.1%}")


if __name__ == "__main__":
    main()
