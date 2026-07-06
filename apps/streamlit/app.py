"""Dashboard Streamlit do CopaMind 2026 (bilíngue EN/PT-BR).

Execute com: `copamind ui serve` ou `streamlit run apps/streamlit/app.py`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from copamind.core.config import get_settings
from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import LMStudioClient
from copamind.llm.config import load_model_specs
from copamind.ui.dashboard import (
    calibration_view,
    championship_table,
    chat_view,
    database_status,
    match_prediction_view,
    pool_leaderboard_view,
    stage_probabilities_view,
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
                tr.t("nav_pool"),
                tr.t("nav_chat"),
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
        elif page == tr.t("nav_pool"):
            _render_pool(repo, tr)
        elif page == tr.t("nav_chat"):
            _render_chat(repo, tr, locale)

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

    st.markdown(f"**{tr.t('bracket_path')}**")
    stage_rows = stage_probabilities_view(repo, iterations=iterations)
    stage_frame = pd.DataFrame(stage_rows).set_index("team_id")
    st.dataframe(
        stage_frame.style.format("{:.1%}"),
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


def _render_pool(repo: DuckDBRepository, tr: Translator) -> None:
    st.subheader(f"🏆 {tr.t('pool_title')}")
    if st.button(tr.t("pool_run")):
        rows = pool_leaderboard_view(repo)
        if not rows:
            st.info(tr.t("pool_empty"))
            return
        frame = pd.DataFrame(rows)
        frame = frame.rename(
            columns={
                "predictor_name": tr.t("predictor"),
                "predictions": tr.t("pool_predictions"),
                "total_points": tr.t("pool_points"),
                "exact_scores": tr.t("pool_exact"),
                "correct_results": tr.t("pool_correct"),
                "mean_brier": tr.t("pool_brier"),
            }
        )
        st.dataframe(frame.set_index(tr.t("predictor")), use_container_width=True)
        st.bar_chart(frame.set_index(tr.t("predictor"))[tr.t("pool_points")])

        st.markdown(f"**{tr.t('calibration_curve')}**")
        reports = calibration_view(repo)
        for report in reports:
            bins = [b for b in report["reliability"] if b["count"] > 0]
            if not bins:
                continue
            curve = pd.DataFrame(
                {
                    tr.t("confidence"): [b["avg_confidence"] for b in bins],
                    tr.t("accuracy"): [b["accuracy"] for b in bins],
                }
            ).set_index(tr.t("confidence"))
            st.caption(
                f"{report['predictor_name']} — Brier {report['brier']:.3f}, ECE {report['ece']:.3f}"
            )
            st.line_chart(curve)
    else:
        st.info(tr.t("pool_empty"))


def _render_chat(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader(f"💬 {tr.t('chat_title')}")
    teams = repo.list_teams()
    options = {t.name: t.team_id for t in teams}
    names = list(options)
    col1, col2 = st.columns(2)
    home = col1.selectbox(tr.t("home"), names, index=0)
    away = col2.selectbox(tr.t("away"), names, index=min(1, len(names) - 1))
    question = st.text_input(tr.t("question"), value="Quem tem mais chance de vencer?")

    if not st.button(tr.t("run_chat")):
        return
    if options[home] == options[away]:
        st.error(tr.t("same_team_error"))
        return

    try:
        specs = load_model_specs()
        settings = get_settings()
        client = LMStudioClient(
            base_url=settings.lmstudio_base_url,
            api_key=settings.lmstudio_api_key,
            timeout=float(settings.lmstudio_timeout_seconds),
        )
        result = chat_view(
            repo,
            client,
            home_id=options[home],
            away_id=options[away],
            question=question,
            analyst=specs["analyst"],
            challenger=specs["challenger"],
            auditor=specs["auditor"],
            response_language=locale,
        )
    except Exception as exc:
        st.warning(f"{tr.t('llm_unavailable')}\n\n{exc}")
        return

    labels = {
        "primary_analyst": tr.t("box_analyst"),
        "alternative_analysis": tr.t("box_challenger"),
        "evidence_auditor": tr.t("box_auditor"),
    }
    for box in result["boxes"]:
        with st.expander(f"{labels.get(box['role'], box['role'])} — {box['model_id']}"):
            if box["error"]:
                st.error(box["error"])
            elif box["response"]:
                st.write(box["response"]["answer"])
            elif box["audit"]:
                st.json(box["audit"])
    st.success(f"**{tr.t('box_consensus')}:** {result['consensus']['answer']}")


if __name__ == "__main__":
    main()
