"""Dashboard Streamlit do CopaMind 2026 (bilíngue EN/PT-BR).

Execute: copamind ui serve   ou   streamlit run apps/streamlit/app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from copamind.core.config import get_settings
from copamind.data.connectors.flags import TEAMS
from copamind.data.repositories import DuckDBRepository
from copamind.models.calibration.report import calibration_report
from copamind.models.ensemble.service import ensemble_match
from copamind.models.poisson.service import predict_match
from copamind.pool.service import run_backtest
from copamind.simulation.service import build_default_config, run_simulation
from copamind.ui.i18n import DEFAULT_LOCALE, Translator, available_locales
from copamind.ui.tournament import build_bracket_html


@st.cache_resource
def _repo_path() -> str:
    return str(get_settings().duckdb_path)


def _open_repo() -> DuckDBRepository:
    repo = DuckDBRepository(_repo_path())
    repo.create_schema()
    return repo


def _team_label(team_id: str, locale: str = "pt-BR") -> str:
    t = TEAMS.get(team_id, {})
    if not t:
        return team_id
    name = t["name_pt"] if locale == "pt-BR" else t["name_en"]
    return f"{t['emoji']} {name}"


def main() -> None:
    st.set_page_config(page_title="CopaMind 2026", page_icon="⚽", layout="wide")

    locales = available_locales()
    locale = st.sidebar.selectbox(
        "🌐 Idioma / Language", locales, index=locales.index(DEFAULT_LOCALE)
    )
    tr = Translator(locale)

    import os

    hero = "docs/assets/copamind-hero.png"
    if os.path.exists(hero):
        st.image(hero, use_container_width=True)
    else:
        st.title(f"⚽ {tr.t('app_title')}")
    st.caption(tr.t("subtitle"))

    with _open_repo() as repo:
        if repo.count("teams") == 0:
            st.warning(f"{tr.t('no_data')} {tr.t('run_ingest_hint')}")
            st.stop()

        page = st.sidebar.radio(
            tr.t("section_status"),
            [
                tr.t("nav_home"),
                "🏆 Copa 2026",
                tr.t("nav_ranking"),
                tr.t("nav_team"),
                tr.t("nav_predict"),
                tr.t("nav_pool"),
                tr.t("nav_chat"),
            ],
        )

        if page == tr.t("nav_home"):
            _render_home(repo, tr)
        elif page == "🏆 Copa 2026":
            _render_copa(repo, tr, locale)
        elif page == tr.t("nav_ranking"):
            _render_ranking(repo, tr, locale)
        elif page == tr.t("nav_team"):
            _render_team(repo, tr, locale)
        elif page == tr.t("nav_predict"):
            _render_predict(repo, tr, locale)
        elif page == tr.t("nav_pool"):
            _render_pool(repo, tr)
        elif page == tr.t("nav_chat"):
            _render_chat(repo, tr, locale)

    st.sidebar.divider()
    st.sidebar.info(tr.t("disclaimer"))


# ── Home ──────────────────────────────────────────────────────────────────────
def _render_home(repo: DuckDBRepository, tr: Translator) -> None:
    st.subheader(tr.t("section_status"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr.t("teams"), repo.count("teams"))
    c2.metric(tr.t("matches"), repo.count("matches"))
    c3.metric(tr.t("predictions"), repo.count("predictions"))
    c4.metric(tr.t("snapshot"), repo.latest_snapshot_id() or "-")


# ── Copa 2026 ─────────────────────────────────────────────────────────────────
def _render_copa(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader("🏆 Copa do Mundo 2026 — ao vivo")
    components.html(build_bracket_html(), height=700, scrolling=True)

    st.markdown("---")
    # Partidas de hoje e amanhã com previsões
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔵 Hoje — Oitavas**")
        _match_prediction_card(repo, "T-POR", "T-ESP", "Hoje 15:00", locale)
        _match_prediction_card(repo, "T-USA", "T-BEL", "Hoje 20:00", locale)
    with c2:
        st.markdown("**🟡 Amanhã — Oitavas**")
        _match_prediction_card(repo, "T-ARG", "T-EGY", "Amanhã 12:00", locale)
        _match_prediction_card(repo, "T-SUI", "T-COL", "Amanhã 16:00", locale)

    st.markdown("---")
    st.markdown("**🟢 Quartas de final confirmadas**")
    cq1, cq2 = st.columns(2)
    with cq1:
        _match_prediction_card(repo, "T-FRA", "T-MAR", "Qui 09/07 16:00", locale)
    with cq2:
        _match_prediction_card(repo, "T-NOR", "T-ENG", "Sáb 11/07 17:00", locale)

    st.markdown("---")
    _render_group_standings(repo, locale)


def _match_prediction_card(
    repo: DuckDBRepository, home_id: str, away_id: str, label: str, locale: str
) -> None:
    home = _team_label(home_id, locale)
    away = _team_label(away_id, locale)
    with st.container(border=True):
        st.caption(label)
        cols = st.columns([5, 1, 5])
        cols[0].markdown(f"**{home}**")
        cols[1].markdown(
            "<div style='text-align:center;padding-top:6px'>x</div>", unsafe_allow_html=True
        )
        cols[2].markdown(f"**{away}**")
        # previsão Poisson
        try:
            finished = repo.list_finished_matches()
            if len(finished) >= 5:
                from copamind.models.poisson.service import build_poisson

                m = build_poisson(repo)
                p = m.predict_match(home_id, away_id, neutral_venue=True)
                cols[0].caption(f"🏠 {p.prob_home_win:.0%}")
                cols[1].caption(f"= {p.prob_draw:.0%}")
                cols[2].caption(f"✈ {p.prob_away_win:.0%}")
        except Exception:
            pass


def _render_group_standings(repo: DuckDBRepository, locale: str) -> None:
    st.markdown("#### Classificação dos grupos")
    groups = sorted({t.get("group", "") for t in TEAMS.values() if t.get("group")})
    # exibe de 4 em 4
    for row_start in range(0, len(groups), 4):
        cols = st.columns(4)
        for gi, group in enumerate(groups[row_start : row_start + 4]):
            with cols[gi]:
                st.markdown(f"**Grupo {group}**")
                team_ids = [tid for tid, t in TEAMS.items() if t.get("group") == group]
                finished = repo.list_finished_matches()
                rows = []
                for tid in team_ids:
                    pts = draws = wins = gf = ga = games = 0
                    for m in finished:
                        if m.home_team_id == tid or m.away_team_id == tid:
                            is_home = m.home_team_id == tid
                            gf += (m.home_score or 0) if is_home else (m.away_score or 0)
                            ga += (m.away_score or 0) if is_home else (m.home_score or 0)
                            h, a = m.home_score or 0, m.away_score or 0
                            wins += 1 if (is_home and h > a) or (not is_home and a > h) else 0
                            draws += 1 if h == a else 0
                            games += 1
                    pts = wins * 3 + draws
                    t_info = TEAMS.get(tid, {})
                    name = t_info.get("name_pt" if locale == "pt-BR" else "name_en", tid)
                    emoji = t_info.get("emoji", "🏳")
                    rows.append({"": f"{emoji} {name}", "J": games, "Pts": pts, "SG": gf - ga})
                rows.sort(key=lambda r: (-r["Pts"], -r["SG"]))
                st.dataframe(pd.DataFrame(rows).set_index(""), use_container_width=True, height=178)


# ── Chances de título ─────────────────────────────────────────────────────────
def _render_ranking(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader(tr.t("championship_chances"))
    iterations = st.slider(tr.t("iterations"), 500, 20000, 5000, step=500)
    config = build_default_config(repo, iterations=iterations)
    result = run_simulation(repo, config)

    rows = []
    for team in result.teams:
        t_info = TEAMS.get(team.team_id, {})
        rows.append(
            {
                "Seleção": f"{t_info.get('emoji', '🏳')} {t_info.get('name_pt' if locale == 'pt-BR' else 'name_en', team.team_id)}"
                if t_info
                else team.team_id,
                tr.t("qualify"): team.qualified_probability,
                tr.t("title"): team.champion_probability,
            }
        )
    frame = pd.DataFrame(rows).set_index("Seleção")
    st.bar_chart(frame[tr.t("title")].sort_values(ascending=False).head(16))
    st.dataframe(frame.style.format("{:.1%}"), use_container_width=True)

    st.markdown(f"**{tr.t('bracket_path')}**")
    stage_rows = []
    for team in result.teams:
        t_info = TEAMS.get(team.team_id, {})
        row: dict = {
            "Seleção": f"{t_info.get('emoji', '🏳')} {t_info.get('name_pt', team.team_id)}"
            if t_info
            else team.team_id
        }
        row.update(team.stage_probabilities)
        row["champion"] = team.champion_probability
        stage_rows.append(row)
    st.dataframe(
        pd.DataFrame(stage_rows).set_index("Seleção").style.format("{:.1%}"),
        use_container_width=True,
    )


# ── Análise de seleção ────────────────────────────────────────────────────────
def _render_team(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader(tr.t("team_analysis"))
    teams = repo.list_teams()
    options: dict[str, str] = {}
    for t in teams:
        t_info = TEAMS.get(t.team_id, {})
        label = (
            f"{t_info.get('emoji', '🏳')} {t_info.get('name_pt' if locale == 'pt-BR' else 'name_en', t.name)}"
            if t_info
            else t.name
        )
        options[label] = t.team_id
    name = st.selectbox(tr.t("select_team"), sorted(options))
    team_id = options[name]

    from copamind.features.service import analyze_team

    analysis = analyze_team(repo, team_id)
    st.metric(tr.t("elo_rating"), f"{analysis.elo_rating:.0f}")
    st.markdown(f"**{tr.t('recent_form')}**")
    st.dataframe(
        pd.DataFrame([w.model_dump() for w in analysis.form.windows]), use_container_width=True
    )

    last = repo.get_last_matches(team_id, limit=5)
    rows = []
    for m in last:
        h = TEAMS.get(m.home_team_id, {})
        a_i = TEAMS.get(m.away_team_id, {})
        rows.append(
            {
                "Data": m.match_date.strftime("%d/%m"),
                "Casa": f"{h.get('emoji', '🏳')} {h.get('name_pt', m.home_team_id)}"
                if h
                else m.home_team_id,
                "Placar": f"{m.home_score}-{m.away_score}",
                "Fora": f"{a_i.get('emoji', '🏳')} {a_i.get('name_pt', m.away_team_id)}"
                if a_i
                else m.away_team_id,
            }
        )
    if rows:
        st.markdown(f"**{tr.t('last_matches')}**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ── Previsão de partida ───────────────────────────────────────────────────────
def _render_predict(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader(tr.t("match_prediction"))
    teams = repo.list_teams()
    options: dict[str, str] = {}
    for t in teams:
        t_info = TEAMS.get(t.team_id, {})
        label = (
            f"{t_info.get('emoji', '🏳')} {t_info.get('name_pt' if locale == 'pt-BR' else 'name_en', t.name)}"
            if t_info
            else t.name
        )
        options[label] = t.team_id
    names = sorted(options)
    col1, col2 = st.columns(2)
    home_l = col1.selectbox(tr.t("home"), names, index=0)
    away_l = col2.selectbox(tr.t("away"), names, index=min(1, len(names) - 1))
    neutral = st.checkbox(tr.t("neutral"), value=True)

    if st.button(tr.t("predict_button")):
        home_id, away_id = options[home_l], options[away_l]
        if home_id == away_id:
            st.error(tr.t("same_team_error"))
            return
        pred = predict_match(repo, home_id, away_id, neutral_venue=neutral, persist=False)
        ens = ensemble_match(repo, home_id, away_id, neutral_venue=neutral)
        home_name = _team_label(home_id, locale)
        away_name = _team_label(away_id, locale)
        st.markdown(f"### {home_name} x {away_name}")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"🏠 {home_name} (Poisson)", f"{pred.prob_home_win:.1%}")
        c2.metric("= Empate", f"{pred.prob_draw:.1%}")
        c3.metric(f"✈ {away_name} (Poisson)", f"{pred.prob_away_win:.1%}")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"🏠 {home_name} (Ensemble)", f"{ens.prob_home:.1%}")
        c2.metric("= Empate", f"{ens.prob_draw:.1%}")
        c3.metric(f"✈ {away_name} (Ensemble)", f"{ens.prob_away:.1%}")
        score = pred.most_likely_score
        st.info(
        st.info(
            f"🎯 {tr.t('most_likely_score')}: **{score[0]}-{score[1]}**"
            f" | Gols: {pred.expected_home_goals:.2f} x {pred.expected_away_goals:.2f}"
            f" | Over 2.5: {pred.prob_over_2_5:.1%}"
        )
        )


# ── Bolão ─────────────────────────────────────────────────────────────────────
def _render_pool(repo: DuckDBRepository, tr: Translator) -> None:
    st.subheader(f"🏆 {tr.t('pool_title')}")
    if st.button(tr.t("pool_run")):
        summary = run_backtest(repo)
        if not summary.standings:
            st.info(tr.t("pool_empty"))
            return
        frame = pd.DataFrame([s.model_dump() for s in summary.standings]).rename(
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

        reports = calibration_report(repo)
        if reports:
            st.markdown(f"**{tr.t('calibration_curve')}**")
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


# ── Chat ──────────────────────────────────────────────────────────────────────
def _render_chat(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader(f"💬 {tr.t('chat_title')}")
    teams = repo.list_teams()
    options: dict[str, str] = {}
    for t in teams:
        t_info = TEAMS.get(t.team_id, {})
        label = (
            f"{t_info.get('emoji', '🏳')} {t_info.get('name_pt' if locale == 'pt-BR' else 'name_en', t.name)}"
            if t_info
            else t.name
        )
        options[label] = t.team_id
    names = sorted(options)
    col1, col2 = st.columns(2)
    home_l = col1.selectbox(tr.t("home"), names, index=0)
    away_l = col2.selectbox(tr.t("away"), names, index=min(1, len(names) - 1))
    question = st.text_input(tr.t("question"), value="Quem tem mais chance de vencer?")

    if not st.button(tr.t("run_chat")):
        return
    if options[home_l] == options[away_l]:
        st.error(tr.t("same_team_error"))
        return
    try:
        from copamind.llm.client import LMStudioClient
        from copamind.llm.config import load_model_specs
        from copamind.llm.orchestrator import SequentialOrchestrator, build_evidence_pack

        settings = get_settings()
        specs = load_model_specs()
        client = LMStudioClient(
            base_url=settings.lmstudio_base_url,
            api_key=settings.lmstudio_api_key,
            timeout=float(settings.lmstudio_timeout_seconds),
        )
        pack = build_evidence_pack(repo, options[home_l], options[away_l])
        result = SequentialOrchestrator(
            client, specs["analyst"], specs["challenger"], specs["auditor"]
        ).run(question, pack, response_language=locale)
    except Exception as exc:
        st.warning(f"{tr.t('llm_unavailable')}\n\n{exc}")
        return

    labels = {
        "primary_analyst": f"🔵 {tr.t('box_analyst')}",
        "alternative_analysis": f"🟣 {tr.t('box_challenger')}",
        "evidence_auditor": f"🔍 {tr.t('box_auditor')}",
    }
    for box in result.boxes:
        with st.expander(f"{labels.get(box['role'], box['role'])} — {box['model_id']}"):
            if box["error"]:
                st.error(box["error"])
            elif box["response"]:
                st.write(box["response"]["answer"])
            elif box["audit"]:
                st.json(box["audit"])
    st.success(f"**{tr.t('box_consensus')}:** {result.consensus['answer']}")


if __name__ == "__main__":
    main()
