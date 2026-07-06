"""Dashboard Streamlit do CopaMind 2026 (bilíngue EN/PT-BR).

Execute: copamind ui serve   ou   streamlit run apps/streamlit/app.py
"""

from __future__ import annotations

import os

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
from copamind.ui.backgrounds import clear_bg_css, home_bg_css, page_bg_css
from copamind.ui.i18n import DEFAULT_LOCALE, Translator, available_locales
from copamind.ui.styles import inject_css
from copamind.ui.tournament import build_bracket_html

_POS_ORDER = {"GK": 0, "CB": 1, "RB": 2, "LB": 3, "CDM": 4, "CM": 5, "CAM": 6, "RW": 7, "LW": 8, "CF": 9, "ST": 10}


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


def _sidebar_logo() -> None:
    icon = "docs/assets/icon.png"
    logo = "docs/assets/copamind_2026.png"
    if os.path.exists(icon):
        st.sidebar.image(icon, width=64)
    if os.path.exists(logo):
        st.sidebar.image(logo, use_container_width=True)
    else:
        st.sidebar.markdown("### ⚽ CopaMind **2026**")
    st.sidebar.markdown("---")


def main() -> None:
    st.set_page_config(
        page_title="CopaMind 2026",
        page_icon="docs/assets/icon.png" if os.path.exists("docs/assets/icon.png") else "⚽",
        layout="wide",
    )
    inject_css()

    locales = available_locales()
    locale = st.sidebar.selectbox(
        "🌐 Idioma / Language", locales, index=locales.index(DEFAULT_LOCALE)
    )
    tr = Translator(locale)
    _sidebar_logo()

    with _open_repo() as repo:
        if repo.count("teams") == 0:
            st.warning(f"{tr.t('no_data')} {tr.t('run_ingest_hint')}")
            st.stop()

        page = st.sidebar.radio(
            tr.t("section_status"),
            [
                tr.t("nav_home"),
                "🏆 Copa 2026",
                "⚽ Resultados",
                "📊 Estatísticas",
                tr.t("nav_ranking"),
                tr.t("nav_team"),
                tr.t("nav_predict"),
                "🤖 Bolão das IAs",
                tr.t("nav_chat"),
            ],
        )

        # ── Fundo por página ───────────────────────────────────────────────
        if page == tr.t("nav_home"):
            st.markdown(home_bg_css(), unsafe_allow_html=True)
        elif page in ("🏆 Copa 2026", "⚽ Resultados"):
            st.markdown(page_bg_css(2), unsafe_allow_html=True)   # estádio
        elif page in ("📊 Estatísticas", "🤖 Bolão das IAs"):
            st.markdown(page_bg_css(1), unsafe_allow_html=True)   # clean1
        else:
            st.markdown(clear_bg_css(), unsafe_allow_html=True)

        # ── Roteamento ────────────────────────────────────────────────────
        if page == tr.t("nav_home"):
            _render_home(repo, tr)
        elif page == "🏆 Copa 2026":
            _render_copa(repo, tr, locale)
        elif page == "⚽ Resultados":
            _render_resultados(repo, tr, locale)
        elif page == "📊 Estatísticas":
            _render_stats(repo, tr, locale)
        elif page == tr.t("nav_ranking"):
            _render_ranking(repo, tr, locale)
        elif page == tr.t("nav_team"):
            _render_team(repo, tr, locale)
        elif page == tr.t("nav_predict"):
            _render_predict(repo, tr, locale)
        elif page == "🤖 Bolão das IAs":
            _render_pool(repo, tr)
        elif page == tr.t("nav_chat"):
            _render_chat(repo, tr, locale)

    st.sidebar.divider()
    st.sidebar.info(tr.t("disclaimer"))


# ── Home — tela inicial com fundo_taça ───────────────────────────────────────
def _render_home(repo: DuckDBRepository, tr: Translator) -> None:
    # Logo / banner centrado
    banner = "docs/assets/copamind_2026.png"
    hero   = "docs/assets/copamind-hero.png"
    if os.path.exists(banner):
        c = st.columns([1, 3, 1])
        c[1].image(banner, use_container_width=True)
    elif os.path.exists(hero):
        st.image(hero, use_container_width=True)

    st.markdown(
        "<div style='text-align:center;margin-bottom:24px'>"
        "<p style='color:#9eb5b1;letter-spacing:.2em;text-transform:uppercase;"
        "font-size:13px'>Local AI · ML · RAG · MCP · Agents</p></div>",
        unsafe_allow_html=True,
    )

    # Métricas do torneio
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⚽ Seleções", repo.count("teams"))
    c2.metric("📋 Partidas", repo.count("matches"))
    c3.metric("🔮 Previsões", repo.count("predictions"))
    c4.metric("👤 Jogadores", repo.count("player_ratings"))

    st.markdown("---")
    # Jogos de hoje em destaque
    st.markdown(
        "<div class='eyebrow'>Hoje · Oitavas de final</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        _match_hero_card("T-POR", "T-ESP", "🔵 Hoje 15:00")
    with c2:
        _match_hero_card("T-USA", "T-BEL", "🔵 Hoje 20:00")

    st.markdown(
        "<div class='eyebrow' style='margin-top:16px'>Amanhã · Oitavas de final</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        _match_hero_card("T-ARG", "T-EGY", "🟡 Amanhã 12:00")
    with c2:
        _match_hero_card("T-SUI", "T-COL", "🟡 Amanhã 16:00")


def _match_hero_card(home_id: str, away_id: str, label: str) -> None:
    """Card de destaque de partida com previsão rápida."""
    h = TEAMS.get(home_id, {}); a = TEAMS.get(away_id, {})
    h_name = h.get("name_pt", home_id); a_name = a.get("name_pt", away_id)
    h_flag = h.get("emoji", "🏳"); a_flag = a.get("emoji", "🏳")

    with st.container(border=True):
        st.caption(label)
        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"padding:8px 0'>"
            f"<span style='font-size:24px'>{h_flag}</span>"
            f"<strong style='font-size:16px'>{h_name}</strong>"
            f"<span style='color:#9eb5b1;font-weight:700;padding:0 12px'>×</span>"
            f"<strong style='font-size:16px'>{a_name}</strong>"
            f"<span style='font-size:24px'>{a_flag}</span></div>",
            unsafe_allow_html=True,
        )


# ── Resultados — tabela completa + alimentar placar ───────────────────────────
def _render_resultados(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader("⚽ Partidas da Copa 2026")
    tab_feed, tab_all = st.tabs(["➕ Alimentar resultado", "📋 Todas as partidas"])

    with tab_feed:
        _render_result_entry(repo, locale)

    with tab_all:
        _render_all_matches(repo, locale)


def _render_result_entry(repo: DuckDBRepository, locale: str) -> None:
    """Formulário para inserir placar de partidas agendadas."""
    scheduled = [m for m in repo.list_matches(limit=200) if m.status.value == "scheduled"]
    if not scheduled:
        st.success("Todas as partidas já têm resultado registrado!")
        return

    options = {}
    for m in scheduled:
        h = TEAMS.get(m.home_team_id, {}); a = TEAMS.get(m.away_team_id, {})
        h_name = h.get("name_pt", m.home_team_id); a_name = a.get("name_pt", m.away_team_id)
        h_flag = h.get("emoji", "🏳"); a_flag = a.get("emoji", "🏳")
        label = f"{h_flag} {h_name} × {a_flag} {a_name}  ({m.match_date.strftime('%d/%m')})"
        options[label] = m

    selected_label = st.selectbox("Selecione a partida", list(options))
    match = options[selected_label]

    h = TEAMS.get(match.home_team_id, {})
    a_i = TEAMS.get(match.away_team_id, {})
    h_name = h.get("name_pt", match.home_team_id); a_name = a_i.get("name_pt", match.away_team_id)

    with st.form("result_form"):
        c1, c2, c3 = st.columns([3, 1, 3])
        c1.markdown(f"**{h.get('emoji','')} {h_name}**")
        home_score = c1.number_input("Gols mandante", min_value=0, max_value=30, step=1, value=0)
        c2.markdown("<div style='text-align:center;padding-top:32px;font-size:20px'>×</div>", unsafe_allow_html=True)
        away_score = c3.number_input("Gols visitante", min_value=0, max_value=30, step=1, value=0)
        c3.markdown(f"**{a_i.get('emoji','')} {a_name}**")
        submitted = st.form_submit_button("💾 Registrar resultado", use_container_width=True)

    if submitted:
        _record_match_result(repo, match.match_id, int(home_score), int(away_score))
        st.success(f"✅ {h_name} {home_score}–{away_score} {a_name} registrado!")
        st.rerun()


def _record_match_result(repo: DuckDBRepository, match_id: str, home_score: int, away_score: int) -> None:
    """Atualiza o placar na base e registra no bolão."""
    from datetime import UTC, datetime

    from copamind.data.schemas import MatchStatus, PoolResult

    repo._con.execute(
        "UPDATE matches SET home_score=?, away_score=?, status=? WHERE match_id=?",
        [home_score, away_score, str(MatchStatus.finished), match_id],
    )
    repo.upsert_pool_result(
        PoolResult(
            match_id=match_id,
            home_score=home_score,
            away_score=away_score,
            recorded_at=datetime.now(UTC),
        )
    )


def _render_all_matches(repo: DuckDBRepository, locale: str) -> None:
    """Tabela completa de todas as partidas com filtros."""
    all_matches = repo.list_matches(limit=500)
    if not all_matches:
        st.info("Sem partidas na base.")
        return

    stages = sorted({m.stage.value for m in all_matches})
    stage_filter = st.selectbox("Filtrar por fase", ["Todas", *stages])

    rows = []
    for m in all_matches:
        if stage_filter != "Todas" and m.stage.value != stage_filter:
            continue
        h = TEAMS.get(m.home_team_id, {}); a = TEAMS.get(m.away_team_id, {})
        h_flag = h.get("emoji", "🏳"); a_flag = a.get("emoji", "🏳")
        h_name = h.get("name_pt" if locale == "pt-BR" else "name_en", m.home_team_id)
        a_name = a.get("name_pt" if locale == "pt-BR" else "name_en", m.away_team_id)
        score = f"**{m.home_score}–{m.away_score}**" if m.home_score is not None else "–"
        status_icon = "✅" if m.status.value == "finished" else "🕐"
        rows.append({
            "Data": m.match_date.strftime("%d/%m"),
            "Fase": m.stage.value,
            "Casa": f"{h_flag} {h_name}",
            "Placar": score,
            "Fora": f"{a_flag} {a_name}",
            "": status_icon,
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
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


# ── Estatísticas de jogadores e seleções ──────────────────────────────────────
def _render_stats(repo: DuckDBRepository, tr: Translator, locale: str) -> None:
    st.subheader("📊 Estatísticas — Jogadores & Seleções")
    n_players = repo.count("player_ratings")
    if n_players == 0:
        st.info("Sem dados de jogadores. Execute: `copamind ingest players data/samples/copa2026_players.json`")
        if st.button("▶ Carregar jogadores agora"):
            from copamind.data.ingestion.service import ingest_players
            count = ingest_players(repo, "data/samples/copa2026_players.json")
            st.success(f"{count} jogadores carregados!")
            st.rerun()
        return

    tab1, tab2, tab3, tab4 = st.tabs(["🥇 Artilharia", "⭐ Melhores ratings", "🔍 Por seleção", "⚖️ Comparar"])

    with tab1:
        st.markdown("### 🥇 Artilheiros da Copa 2026")
        scorers = repo.top_scorers(limit=20)
        rows = []
        for p in scorers:
            t_info = TEAMS.get(p.team_id, {})
            flag = t_info.get("emoji", "🏳")
            rows.append({
                "": f"{flag} {t_info.get('name_pt' if locale == 'pt-BR' else 'name_en', p.team_id)}",
                "Jogador": p.name,
                "Pos": p.position,
                "⚽ Gols": p.copa_goals,
                "🎯 Assist": p.copa_assists,
                "🎮 Jogos": p.copa_matches,
                "OVR": p.overall,
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### ⭐ Top 20 — Rating Geral (EA FC)")
        top = repo.list_players(limit=20)
        rows = []
        for p in top:
            t_info = TEAMS.get(p.team_id, {})
            flag = t_info.get("emoji", "🏳")
            rows.append({
                "OVR": p.overall,
                "": f"{flag}",
                "Jogador": p.name,
                "Pos": p.position,
                "Seleção": t_info.get("name_pt" if locale == "pt-BR" else "name_en", p.team_id),
                "Idade": p.age,
                "PAC": p.pace,
                "SHO": p.shooting,
                "PAS": p.passing,
                "DRI": p.dribbling,
                "DEF": p.defending,
                "PHY": p.physical,
            })
        if rows:
            df = pd.DataFrame(rows).sort_values("OVR", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### 🔍 Elenco por seleção")
        teams = repo.list_teams()
        options: dict[str, str] = {}
        for t in teams:
            t_info = TEAMS.get(t.team_id, {})
            label = f"{t_info.get('emoji', '🏳')} {t_info.get('name_pt' if locale == 'pt-BR' else 'name_en', t.name)}" if t_info else t.name
            options[label] = t.team_id
        selected = st.selectbox("Seleção", sorted(options))
        team_id = options[selected]
        players = repo.list_players(team_id=team_id)
        if not players:
            st.info("Sem jogadores cadastrados para esta seleção.")
        else:
            players_sorted = sorted(players, key=lambda p: _POS_ORDER.get(p.position, 99))
            rows = [{"Pos": p.position, "Jogador": p.name, "Idade": p.age, "OVR": p.overall,
                     "PAC": p.pace, "SHO": p.shooting, "PAS": p.passing,
                     "DRI": p.dribbling, "DEF": p.defending, "PHY": p.physical,
                     "⚽": p.copa_goals, "🎯": p.copa_assists} for p in players_sorted]
            df = pd.DataFrame(rows)
            # rating bar colorida
            st.dataframe(
                df.style.background_gradient(subset=["OVR"], cmap="RdYlGn", vmin=60, vmax=99),
                use_container_width=True, hide_index=True,
            )
            # radar estilo EA
            if len(players_sorted) > 0:
                best = max(players_sorted, key=lambda p: p.overall)
                _player_card(best)

    with tab4:
        st.markdown("### ⚖️ Comparar dois jogadores")
        all_players = repo.list_players()
        if len(all_players) < 2:
            st.info("Sem dados suficientes.")
        else:
            names = sorted({p.name for p in all_players})
            c1, c2 = st.columns(2)
            p1_name = c1.selectbox("Jogador 1", names, index=0)
            p2_name = c2.selectbox("Jogador 2", names, index=min(1, len(names) - 1))
            p1 = next((p for p in all_players if p.name == p1_name), None)
            p2 = next((p for p in all_players if p.name == p2_name), None)
            if p1 and p2:
                attrs = ["overall", "pace", "shooting", "passing", "dribbling", "defending", "physical"]
                labels = ["OVR", "PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
                df = pd.DataFrame({
                    "Atributo": labels,
                    p1.name: [getattr(p1, a) for a in attrs],
                    p2.name: [getattr(p2, a) for a in attrs],
                }).set_index("Atributo")
                st.dataframe(df, use_container_width=True)
                st.bar_chart(df)


def _player_card(p: object) -> None:
    """Exibe um mini-card estilo EA FC para um jogador."""
    t_info = TEAMS.get(p.team_id, {})  # type: ignore[attr-defined]
    flag = t_info.get("emoji", "🏳")
    with st.container(border=True):
        cols = st.columns([1, 3, 1, 1, 1, 1, 1, 1])
        cols[0].markdown(f"### {p.overall}")  # type: ignore[attr-defined]
        cols[1].markdown(f"**{p.name}** {flag}  \n`{p.position}` · {p.age} anos")  # type: ignore[attr-defined]
        for col, label, attr in zip(
            cols[2:], ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"],
            ["pace", "shooting", "passing", "dribbling", "defending", "physical"],
            strict=True,
        ):
            val = getattr(p, attr)  # type: ignore[attr-defined]
            color = "#19e3c2" if val >= 85 else ("#2f6bff" if val >= 75 else "#8fa3bd")
            col.markdown(f"<span style='color:{color};font-size:11px'>{label}</span><br><strong>{val}</strong>", unsafe_allow_html=True)


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
    st.subheader("🤖 Bolão das IAs — Copa 2026")

    tab_pred, tab_board, tab_calib = st.tabs(["🔮 Previsões por partida", "🏆 Leaderboard", "📈 Calibração"])

    # ── Previsões por partida ────────────────────────────────────────────────
    with tab_pred:
        _render_pool_predictions(repo)

    # ── Leaderboard ──────────────────────────────────────────────────────────
    with tab_board:
        if st.button("▶ Calcular pontuação do bolão"):
            summary = run_backtest(repo)
            if summary.standings:
                _render_pool_leaderboard_cards(summary.standings)
            else:
                st.info("Sem partidas com resultado registrado ainda.")
        else:
            st.info("Clique em 'Calcular' para gerar o leaderboard com os resultados atuais.")

    # ── Calibração ───────────────────────────────────────────────────────────
    with tab_calib:
        reports = calibration_report(repo)
        if reports:
            for report in reports:
                bins = [b for b in report["reliability"] if b["count"] > 0]
                if not bins:
                    continue
                curve = pd.DataFrame({
                    "Confiança": [b["avg_confidence"] for b in bins],
                    "Acurácia":  [b["accuracy"] for b in bins],
                }).set_index("Confiança")
                st.caption(f"**{report['predictor_name']}** — Brier {report['brier']:.3f} · ECE {report['ece']:.3f}")
                st.line_chart(curve)
        else:
            st.info("Rode o bolão (aba Leaderboard) para gerar os dados de calibração.")


def _render_pool_predictions(repo: DuckDBRepository) -> None:
    """Cards de previsão estilo EA FC para os jogos restantes."""
    upcoming_matches = [
        ("T-POR", "T-ESP", "Hoje 15:00"),
        ("T-USA", "T-BEL", "Hoje 20:00"),
        ("T-ARG", "T-EGY", "Amanhã 12:00"),
        ("T-SUI", "T-COL", "Amanhã 16:00"),
        ("T-FRA", "T-MAR", "Qui 09/07 — QF"),
        ("T-NOR", "T-ENG", "Sáb 11/07 — QF"),
    ]

    try:
        from copamind.features.service import build_elo
        from copamind.models.poisson.service import build_poisson
        poisson_model = build_poisson(repo)
        elo_system = build_elo(repo)
    except Exception:
        st.warning("Sem dados suficientes para gerar previsões.")
        return

    for home_id, away_id, label in upcoming_matches:
        h_info = TEAMS.get(home_id, {}); a_info = TEAMS.get(away_id, {})
        if not h_info or not a_info:
            continue
        h_name = h_info["name_pt"]; a_name = a_info["name_pt"]
        h_flag = h_info["emoji"]; a_flag = a_info["emoji"]

        st.markdown(
            f"<div style='margin:16px 0 8px'>"
            f"<span style='color:#52e3b5;font-size:11px;font-weight:900;"
            f"letter-spacing:.18em;text-transform:uppercase'>{label}</span> "
            f"<strong style='font-size:18px'>{h_flag} {h_name} × {a_flag} {a_name}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Gera previsões dos 3 modelos
        preds = _generate_preds_for_match(home_id, away_id, poisson_model, elo_system, repo)
        cards_html = _build_pred_cards_html(preds, h_flag, h_name, a_flag, a_name)
        components.html(cards_html, height=310, scrolling=False)
        st.markdown("<hr style='border-color:#1e3232'>", unsafe_allow_html=True)


def _generate_preds_for_match(
    home_id: str, away_id: str, poisson_model: object, elo_system: object, repo: DuckDBRepository
) -> list[dict]:
    from copamind.models.elo import EloRatingSystem
    from copamind.models.ensemble.service import ensemble_match
    from copamind.models.poisson import PoissonModel

    results = []
    try:
        pm: PoissonModel = poisson_model  # type: ignore[assignment]
        pred = pm.predict_match(home_id, away_id, neutral_venue=True)
        results.append({
            "name": "Poisson / Dixon-Coles", "tag": "ML Estatístico", "rank": 1,
            "color": "#52e3b5",
            "prob_home": pred.prob_home_win, "prob_draw": pred.prob_draw,
            "prob_away": pred.prob_away_win,
            "score": f"{pred.most_likely_score[0]}–{pred.most_likely_score[1]}",
            "xg_home": pred.expected_home_goals, "xg_away": pred.expected_away_goals,
        })
    except Exception:
        pass
    try:
        elo: EloRatingSystem = elo_system  # type: ignore[assignment]
        ph = elo.win_probability(home_id, away_id, neutral_venue=True)
        results.append({
            "name": "Elo Rating", "tag": "Rating Histórico", "rank": 2,
            "color": "#f6c453",
            "prob_home": ph * 0.74, "prob_draw": 0.26, "prob_away": (1 - ph) * 0.74,
            "score": "–", "xg_home": 0.0, "xg_away": 0.0,
        })
    except Exception:
        pass
    try:
        ens = ensemble_match(repo, home_id, away_id, neutral_venue=True)
        results.append({
            "name": "Ensemble (Elo + Poisson)", "tag": "Média Ponderada", "rank": 3,
            "color": "#8e7cff",
            "prob_home": ens.prob_home, "prob_draw": ens.prob_draw, "prob_away": ens.prob_away,
            "score": "–", "xg_home": 0.0, "xg_away": 0.0,
        })
    except Exception:
        pass
    return results


def _build_pred_cards_html(
    preds: list[dict], h_flag: str, h_name: str, a_flag: str, a_name: str
) -> str:
    cards = ""
    for p in preds:
        c = p["color"]
        ph = p["prob_home"]; pd_val = p["prob_draw"]; pa = p["prob_away"]
        xg = f"xG {p['xg_home']:.2f} × {p['xg_away']:.2f}" if p["xg_home"] > 0 else ""
        cards += f"""
        <div style="min-width:240px;max-width:280px;border:1px solid rgba(255,255,255,.1);
            border-top:3px solid {c};border-radius:14px;
            background:linear-gradient(160deg,rgba(16,26,26,.98),rgba(8,14,14,.98));
            padding:16px;box-shadow:0 12px 30px rgba(0,0,0,.4);
            display:flex;flex-direction:column;gap:10px">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <span style="color:{c};font-size:10px;font-weight:900;letter-spacing:.15em;
                text-transform:uppercase">{p['tag']}</span>
            <span style="background:rgba(255,255,255,.06);color:#9eb5b1;
                border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700">#{p['rank']}</span>
          </div>
          <div style="color:#f2faf8;font-weight:700;font-size:14px">{p['name']}</div>
          <div style="display:flex;align-items:center;justify-content:space-around;
              background:rgba(255,255,255,.04);border-radius:10px;padding:10px 6px;gap:4px">
            <div style="text-align:center">
              <div style="font-size:22px">{h_flag}</div>
              <div style="color:{c};font-size:20px;font-weight:900">{ph:.0%}</div>
              <div style="color:#9eb5b1;font-size:10px">{h_name}</div>
            </div>
            <div style="text-align:center">
              <div style="color:#9eb5b1;font-size:16px;font-weight:700">{pd_val:.0%}</div>
              <div style="color:#9eb5b1;font-size:10px">Empate</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:22px">{a_flag}</div>
              <div style="color:{c};font-size:20px;font-weight:900">{pa:.0%}</div>
              <div style="color:#9eb5b1;font-size:10px">{a_name}</div>
            </div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="color:#9eb5b1;font-size:11px">Placar mais provável</span>
            <span style="color:{c};font-weight:900;font-size:15px">{p['score']}</span>
          </div>
          {"<div style='color:#9eb5b1;font-size:10px;text-align:right'>" + xg + "</div>" if xg else ""}
        </div>"""

    return f"""
    <style>
      .pred-grid{{display:flex;gap:14px;flex-wrap:wrap;padding:4px 0 8px}}
    </style>
    <div class="pred-grid">{cards}</div>"""


def _render_pool_leaderboard_cards(standings: list) -> None:
    """Leaderboard dos preditores com cards estilo EA."""
    medals = ["🥇", "🥈", "🥉"]
    colors = ["#f6c453", "#c7d4d2", "#d89567"]
    cols = st.columns(min(len(standings), 3))
    for i, standing in enumerate(standings):
        c = colors[i] if i < 3 else "#52e3b5"
        medal = medals[i] if i < 3 else f"#{i+1}"
        with cols[i % len(cols)]:
            st.markdown(
                f"""<div style="border:1px solid {c};border-top:4px solid {c};border-radius:14px;
                padding:18px;background:rgba(16,26,26,.9);text-align:center;margin-bottom:12px">
                <div style="font-size:28px">{medal}</div>
                <div style="font-size:16px;font-weight:800;color:#f2faf8;margin:8px 0 4px">
                    {standing.predictor_name}</div>
                <div style="font-size:32px;font-weight:900;color:{c}">{standing.total_points}</div>
                <div style="color:#9eb5b1;font-size:11px;margin-top:4px">pontos</div>
                <hr style="border-color:#29403f;margin:10px 0">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;font-size:11px">
                  <div><span style="color:#9eb5b1">Palpites</span><br>
                       <strong>{standing.predictions}</strong></div>
                  <div><span style="color:#9eb5b1">Placar certo</span><br>
                       <strong>{standing.exact_scores}</strong></div>
                  <div><span style="color:#9eb5b1">Brier</span><br>
                       <strong>{standing.mean_brier:.3f}</strong></div>
                </div></div>""",
                unsafe_allow_html=True,
            )


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
