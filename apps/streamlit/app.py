"""CopaMind 2026 Streamlit portal."""

from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st

from copamind.core.config import get_settings
from copamind.data.fifa_fixtures import FIFAFixtureConnector
from copamind.data.fifa_statistics_refresh import refresh_all_fifa_data
from copamind.data.fifa_stats import (
    available_summary,
    flag_url,
    player_metric_leaders,
    team_label,
    team_summary,
    top_players,
)
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match, MatchStatus, PoolPrediction, PoolResult
from copamind.features.match_features import KNOCKOUT_PHASES, refresh_knockout_feature_snapshots
from copamind.llm.client import LLMError, LMStudioClient
from copamind.llm.config import load_model_specs
from copamind.pool.llm_agent import (
    BolaoLLMAgent,
    LLMMatchPick,
    LLMModelConsensus,
    LLMRunResult,
    LocalModelInfo,
    build_bolao_prompt,
    build_combo_pick,
    build_match_context,
    build_model_consensus_from_runs,
    classify_local_model,
    run_model_sample_results,
)
from copamind.pool.llm_agent import (
    round_id as new_round_id,
)
from copamind.pool.predictors import EloPredictor, PoissonPredictor
from copamind.pool.scoring import bolao_points, brier_score, outcome
from copamind.pool.service import leaderboard, lock_match_predictions, run_backtest
from copamind.ui.styles import CSS
from copamind.ui.tournament import build_bracket_html

ACCENT = "#38d6a5"
BLUE = "#57a7ff"
GOLD = "#f2c94c"
RED = "#ff7b72"
PURPLE = "#9b8cff"

STAGE_ORDER = {
    "group": 1,
    "round_of_32": 2,
    "round_of_16": 3,
    "quarterfinal": 4,
    "semifinal": 5,
    "third_place": 6,
    "final": 7,
}

STAGE_LABELS = {
    "group": "Grupo",
    "round_of_32": "32 avos",
    "round_of_16": "Oitavas",
    "quarterfinal": "Quartas",
    "semifinal": "Semifinal",
    "third_place": "3o lugar",
    "final": "Final",
    "friendly": "Amistoso",
    "qualifier": "Eliminatoria",
}

@st.cache_resource
def _db_path() -> str:
    return str(get_settings().duckdb_path)


def _repo() -> DuckDBRepository:
    repo = DuckDBRepository(_db_path())
    repo.create_schema()
    return repo


def _inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    clean = _asset_data_url("docs/assets/fundo_clean2.png")
    cup = _asset_data_url("docs/assets/fundo_taca.png")
    clean1 = _asset_data_url("docs/assets/fundo_clean1.png")
    extra = "<style>"
    if clean:
        extra += (
            '[data-testid="stApp"]{'
            f"background-image:linear-gradient(180deg,rgba(5,10,12,.78),rgba(5,10,12,.95)),url('{clean}') !important;"
            "background-size:cover !important;background-attachment:fixed !important;}"
        )
    if clean1:
        extra += (
            ".cm-hero{"
            f"background-image:linear-gradient(135deg,rgba(12,25,24,.94),rgba(10,17,23,.9)),url('{clean1}');"
            "background-size:cover;background-position:center;}"
        )
    if cup:
        extra += (
            ".cm-home-hero{"
            f"background-image:linear-gradient(90deg,rgba(5,12,14,.95) 0%,rgba(5,12,14,.82) 48%,rgba(5,12,14,.35) 100%),url('{cup}');"
            "background-position:center,right center;background-repeat:no-repeat;background-size:cover,contain;"
            "min-height:320px;padding:38px 34px;}"
            ".cm-home-hero p{max-width:620px;}"
        )
    extra += "</style>"
    st.markdown(extra, unsafe_allow_html=True)


def _asset_data_url(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _sidebar() -> str:
    if os.path.exists("docs/assets/copamind_2026.png"):
        st.sidebar.image("docs/assets/copamind_2026.png", width=190)
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navegar",
        ["Home", "Proximos Jogos", "Bolao das LLMs", "Modelos LM Studio", "Dados FIFA", "Ranking"],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Bolao de IAs local com dados oficiais, prompt auditavel e ranking por acerto.")
    return page


def _hero(kicker: str, title: str, subtitle: str, *, home: bool = False) -> None:
    klass = "cm-hero cm-home-hero" if home else "cm-hero"
    st.markdown(
        f"""<section class="{klass}">
<div class="cm-kicker">{escape(kicker)}</div>
<h1>{escape(title)}</h1>
<p>{escape(subtitle)}</p>
</section>""",
        unsafe_allow_html=True,
    )


def _tile(label: str, value: Any, hint: str = "", color: str = ACCENT) -> None:
    st.markdown(
        f"""<div class="cm-stat" style="border-top-color:{color}">
<span>{escape(label)}</span>
<strong>{escape(str(value))}</strong>
<small>{escape(hint)}</small>
</div>""",
        unsafe_allow_html=True,
    )


def _match_label(match: Match) -> str:
    return f"{_date(match)} | {team_label(match.home_team_id)} x {team_label(match.away_team_id)}"


def _date(match: Match) -> str:
    return match.match_date.strftime("%d/%m %H:%M") if match.match_date else "A definir"


def _stage(match: Match) -> str:
    return STAGE_LABELS.get(str(match.stage), str(match.stage))


def _matches(repo: DuckDBRepository) -> list[Match]:
    return sorted(repo.list_matches(limit=800), key=lambda item: item.match_date)


def _upcoming(repo: DuckDBRepository) -> list[Match]:
    return [m for m in _matches(repo) if m.status is MatchStatus.scheduled]


def _finished(repo: DuckDBRepository) -> list[Match]:
    return [m for m in _matches(repo) if m.status is MatchStatus.finished]


def _select_match(
    repo: DuckDBRepository,
    *,
    scheduled_only: bool = True,
    key: str = "match-select",
) -> Match | None:
    matches = _upcoming(repo) if scheduled_only else _matches(repo)
    if scheduled_only and not matches:
        st.caption("Sem jogos abertos. Modo simulacao: escolha uma partida historica.")
        matches = _matches(repo)
    if not matches:
        return None
    labels = {_match_label(match): match for match in matches}
    label = st.selectbox("Partida", list(labels.keys()), label_visibility="collapsed", key=key)
    return labels[label]


def _select_knockout_match(
    repo: DuckDBRepository,
    *,
    scheduled_only: bool = True,
    key: str = "knockout-match-select",
) -> Match | None:
    matches = [match for match in _matches(repo) if str(match.stage) in KNOCKOUT_PHASES]
    if scheduled_only:
        scheduled = [match for match in matches if match.status is MatchStatus.scheduled]
        if scheduled:
            matches = scheduled
        else:
            st.caption("Sem jogos abertos no mata-mata final; exibindo historico para simulacao/backtest.")
    if not matches:
        return None
    labels = {_match_label(match): match for match in sorted(matches, key=lambda item: item.match_date)}
    label = st.selectbox("Partida", list(labels.keys()), label_visibility="collapsed", key=key)
    return labels[label]


def _lm_client() -> LMStudioClient:
    settings = get_settings()
    return LMStudioClient(
        base_url=settings.lmstudio_base_url,
        api_key=settings.lmstudio_api_key,
        timeout=float(settings.lmstudio_timeout_seconds),
    )


def _active_lmstudio_models() -> tuple[list[str], str | None]:
    client = _lm_client()
    try:
        return client.list_models(), None
    except LLMError as exc:
        specs = load_model_specs()
        fallback = sorted({spec.model_id for spec in specs.values()})
        return fallback, str(exc)


def _run_fifa_sync(repo: DuckDBRepository) -> None:
    with st.status("Atualizando jogos, equipes e jogadores FIFA...", expanded=True) as status:
        summary = refresh_all_fifa_data(repo, force_network=True)
        _sync_step("Jogos", summary.fixtures)
        _sync_step("Equipes", summary.team_statistics)
        _sync_step("Jogadores", summary.player_statistics)
        features = refresh_knockout_feature_snapshots(repo)
        st.write(f"Features ML/RAG: {len(features)} snapshots de mata-mata recalculados")
        if summary.warnings:
            status.update(label="Atualizacao concluida com avisos.", state="complete")
        else:
            status.update(label="Base FIFA atualizada.", state="complete")
    st.session_state["last_fifa_sync"] = summary.created_at.isoformat()
    for warning in summary.warnings:
        st.warning(warning)
    st.success("Base FIFA sincronizada. O portal ja esta usando os CSVs atualizados.")


def _sync_step(label: str, item: Any) -> None:
    text = f"{label}: {item.rows} linhas"
    if item.files:
        text += f", {item.files} arquivos"
    text += f" via {item.source}"
    st.write(text)


def render_home() -> None:
    repo = _repo()
    stats = available_summary()
    matches = _matches(repo)
    upcoming = _upcoming(repo)
    standings = leaderboard(repo)
    predictions = repo.list_pool_predictions()

    _hero(
        "CopaMind 2026",
        "Bolao das LLMs da Copa",
        "Modelos locais competem com palpites em JSON, baseline de ML e ranking auditavel. Vamos ver qual modelo vai ganhar.",
        home=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _tile("Partidas", len(matches), f"{len(upcoming)} abertas", BLUE)
    with c2:
        _tile("Stats FIFA", f"{stats['team_tabs']}+{stats['player_tabs']}", "abas equipe+jogador", ACCENT)
    with c3:
        _tile("Jogadores", stats["player_rows"], "linhas na aba ataque", PURPLE)
    with c4:
        _tile("Palpites", len(predictions), "travados", GOLD)
    with c5:
        _tile("Modelos", len(standings), "pontuados", RED)

    if os.path.exists("docs/assets/banner.png"):
        st.image("docs/assets/banner.png", use_container_width=True)

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("### Proximas partidas")
        for match in upcoming[:7]:
            _compact_match(match)
        if not upcoming:
            st.success("Nao ha partidas pendentes na base local.")
    with right:
        st.markdown("### Fluxo do produto")
        st.markdown(
            """<div class="cm-flow">
<div><b>1. Dados</b><span>CSV FIFA de equipes, jogadores, fotos, bandeiras e calendario.</span></div>
<div><b>2. RAG</b><span>Contexto enxuto por partida com estatisticas e jogadores-chave.</span></div>
<div><b>3. LLM</b><span>Cada modelo responde no mesmo JSON do bolao oficial.</span></div>
<div><b>4. Ranking</b><span>Placar real gera pontos, Brier score e leaderboard.</span></div>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown("### Lideres")
        if standings:
            for index, standing in enumerate(standings[:5], 1):
                st.markdown(
                    f"""<div class="cm-rank"><b>#{index}</b><span>{escape(standing.predictor_name)}</span><strong>{standing.total_points} pts</strong></div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("Gere palpites e registre resultados para abrir o ranking.")


def render_proximos_jogos() -> None:
    repo = _repo()
    _hero(
        "FIFA + cache local",
        "Proximos jogos para prever",
        "Atualize a base pela FIFA quando quiser; se a rede falhar, o cache local continua alimentando o portal.",
    )
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Atualizar FIFA", use_container_width=True):
            result = FIFAFixtureConnector().refresh(repo, force_network=True)
            if result.warning:
                st.warning(result.warning)
            st.success(f"{result.matches} partidas sincronizadas via {result.source}.")
            st.rerun()
    with c2:
        st.caption("Fonte: pagina oficial FIFA de standings/fixtures da Copa 2026, com cache em data/cache/fifa.")
    tab_matches, tab_bracket, tab_context, tab_result = st.tabs(
        ["Jogos", "Chave Mata-Mata", "Contexto", "Resultado real"]
    )
    with tab_matches:
        st.markdown("### Rodada")
        matches = _upcoming(repo)
        if not matches:
            st.caption("Sem partidas abertas; exibindo historico para simulacao/backtest.")
            matches = list(reversed(_finished(repo)))[:30]
        for match in matches[:30]:
            _match_operational_card(repo, match)
        if not matches:
            st.success("Nenhuma partida cadastrada.")
    with tab_bracket:
        matches = _matches(repo)
        st.components.v1.html(
            build_bracket_html(matches, consensus_by_match=_latest_consensus_labels(repo)),
            height=760,
            scrolling=True,
        )
    with tab_context:
        match = _select_match(repo, key="proximos-context-match")
        if match is None:
            st.info("Sem partidas abertas.")
        else:
            _match_context_panel(repo, match)
    with tab_result:
        match = _select_match(repo, key="proximos-result-match")
        if match is None:
            st.info("Sem partidas abertas.")
        else:
            _result_form(repo, match)


def render_dados_fifa() -> None:
    repo = _repo()
    _hero(
        "Base oficial",
        "Dados FIFA para alimentar o bolao",
        "As abas de equipes e jogadores viraram CSVs locais. Aqui voce valida cobertura, lideres e ativos visuais.",
    )
    if st.button("Atualizar base FIFA", use_container_width=True):
        _run_fifa_sync(repo)
    last_sync = st.session_state.get("last_fifa_sync")
    if last_sync:
        st.caption(f"Ultima atualizacao nesta sessao: {last_sync}")
    stats = available_summary()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _tile("Abas equipe", stats["team_tabs"], "team_statistics", BLUE)
    with c2:
        _tile("Abas jogador", stats["player_tabs"], "player_statistics", PURPLE)
    with c3:
        _tile("Equipes", stats["team_rows"], "ataque.csv", ACCENT)
    with c4:
        _tile("Jogadores", stats["player_rows"], "ataque.csv", GOLD)

    tab_team, tab_players, tab_files = st.tabs(["Selecoes", "Jogadores", "Arquivos"])
    with tab_team:
        teams = repo.list_teams()
        if not teams:
            st.info("Base DuckDB sem selecoes. Rode a ingestao de samples.")
            return
        selected = st.selectbox("Selecao", [team_label(t.team_id) for t in teams])
        team_id = next(t.team_id for t in teams if team_label(t.team_id) == selected)
        _team_stats_panel(team_id)
    with tab_players:
        leaders = player_metric_leaders("scorers", "goals", limit=20)
        rows = [
            {
                "Foto": player["image_url"],
                "Jogador": player["name"],
                "Selecao": player["team"],
                "Pos": player["position"],
                "Gols": player["goals"],
                "Assist": player["assists"],
                "Min": player["minutes"],
            }
            for player in leaders
        ]
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            column_config={"Foto": st.column_config.ImageColumn(width="small")},
        )
    with tab_files:
        st.markdown("#### CSVs gerados")
        st.code(
            "\n".join(
                [
                    "data/fifa/team_statistics/*.csv",
                    "data/fifa/player_statistics/*.csv",
                    "data/cache/fifa/*.json",
                    "data/cache/fifa_gameday/*.json",
                    "src/copamind/data/fifa_statistics_refresh.py",
                    "scripts/fetch_fifa_team_statistics.py",
                    "scripts/fetch_fifa_player_statistics.py",
                ]
            )
        )


def render_bolao_llms() -> None:
    repo = _repo()
    _hero(
        "RAG + JSON + ranking",
        "Rodada do Bolao das LLMs",
        "Todos os modelos de chat ativos no LM Studio recebem o mesmo contexto. Saidas invalidas ficam auditaveis e o combo usa apenas JSON valido.",
    )
    match = _select_knockout_match(repo)
    if match is None:
        st.info("Sem partidas de Oitavas, Quartas, Semifinais ou Final na base local.")
        return

    context = build_match_context(repo, match)
    messages = build_bolao_prompt(context)
    model_ids, model_warning = _active_lmstudio_models()
    model_infos = [classify_local_model(model_id) for model_id in model_ids]
    automatic_models = [info for info in model_infos if info.participates or info.model_class == "heavy"]
    left, right = st.columns([1.05, 1])
    with left:
        _match_header(match)
        st.markdown("### Evidencias RAG")
        evidence_rows = [{"id": item["id"], "tipo": item["type"], "resumo": item["text"][:220]} for item in context["evidence"]]
        st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True)
        st.markdown("### Prompt final")
        st.code(json.dumps(messages, ensure_ascii=False, indent=2), language="json")
    with right:
        st.markdown("### Modelos da rodada")
        if model_warning:
            st.warning(f"LM Studio indisponivel; usando config/models.yaml. {model_warning}")
        st.metric("Ativos", len(model_infos))
        st.metric("Automaticos", len(automatic_models))
        samples = st.number_input(
            "Amostras por modelo",
            min_value=1,
            max_value=3,
            value=1,
            help="Use 1 para rodar os ~30 modelos. Use 3 apenas como consenso avancado.",
            key="single-match-samples",
        )
        runnable = automatic_models
        rows = [
            {
                "Modelo": info.model_id,
                "Classe": info.model_class,
                "Entra": "sim" if info in runnable else "nao",
                "Aviso": info.warning or "",
            }
            for info in model_infos
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("Padrao do reset: 1 chamada por modelo. Com 3 amostras, a palavra final usa consenso deterministico.")
        if st.button("Reexecutar rodada das LLMs", use_container_width=True):
            _run_llm_pool(repo, match, runnable, phase=str(match.stage), samples_per_model=int(samples))
        st.markdown("### Contrato esperado")
        st.code(
            json.dumps(
                {
                    "winner": "home|draw|away",
                    "prob_home": 0.45,
                    "prob_draw": 0.25,
                    "prob_away": 0.30,
                    "predicted_home_goals": 2,
                    "predicted_away_goals": 1,
                    "goes_to_extra_time": False,
                    "goes_to_penalties": False,
                    "penalty_winner": "none|home|away",
                    "first_goal_scorer": "Nome ou null",
                    "player_picks": [{"player_name": "Nome", "team": "Selecao", "market": "gol", "confidence": 0.61}],
                    "confidence": 0.64,
                    "rationale": "Analise curta com evidencias.",
                    "evidence_ids": ["home.team_stats", "away.key_players"],
                },
                indent=2,
            ),
            language="json",
        )
    st.divider()
    _phase_runner_panel(repo, model_infos)


def render_modelos_lmstudio() -> None:
    _hero(
        "LM Studio local",
        "Modelos ativos e compatibilidade",
        "A tela lista tudo que o LM Studio expõe e separa participantes, modelos pesados e embeddings de RAG.",
    )
    model_ids, warning = _active_lmstudio_models()
    if warning:
        st.warning(warning)
    infos = [classify_local_model(model_id) for model_id in model_ids]
    repo = _repo()
    metrics = {row["model_id"]: row for row in repo.llm_model_metrics()}
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _tile("Ativos", len(infos), "LM Studio", BLUE)
    with c2:
        _tile("Bolao", sum(i.model_class == "bolao" for i in infos), "chat leve", ACCENT)
    with c3:
        _tile("Pesados", sum(i.model_class == "heavy" for i in infos), "com aviso", GOLD)
    with c4:
        _tile("RAG", sum(i.model_class == "embedding" for i in infos), "nao competem", PURPLE)
    rows = [
        {
            "Modelo": info.model_id,
            "Classe": info.model_class,
            "Participa": info.participates,
            "Observacao": info.warning or "Pronto para o bolao.",
            "Rodadas": metrics.get(info.model_id, {}).get("total_rounds", 0),
            "Chamadas": metrics.get(info.model_id, {}).get("total_runs", 0),
            "JSON valido": _pct(
                metrics.get(info.model_id, {}).get("valid_runs", 0),
                metrics.get(info.model_id, {}).get("total_runs", 0),
            ),
            "Lat ms": _round_or_dash(metrics.get(info.model_id, {}).get("avg_latency_ms")),
            "Tok/s": _round_or_dash(metrics.get(info.model_id, {}).get("avg_tokens_per_second")),
            "Coerencia": _round_or_dash(metrics.get(info.model_id, {}).get("avg_coherence_score"), 3),
        }
        for info in infos
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_ranking() -> None:
    repo = _repo()
    _hero(
        "Benchmark",
        "Ranking do Bolao de IAs",
        "Cada modelo compete por placar exato, resultado correto e calibracao probabilistica.",
    )
    if st.button("Rodar backtest ML no historico", use_container_width=False):
        summary = run_backtest(repo, [PoissonPredictor(), EloPredictor()])
        st.success(
            f"Backtest concluido: {summary.matches_evaluated} jogos, "
            f"{summary.predictions_locked} palpites novos."
        )
        st.rerun()
    rounds = repo.list_llm_pool_rounds()
    batches = repo.list_llm_phase_batches()
    round_options = {"Todas as rodadas": None} | {
        f"{row['created_at']} | {row['round_id']}": row["round_id"] for row in rounds
    }
    phase_options = {"Todas as fases": None} | {
        label: stage for stage, label in STAGE_LABELS.items() if stage in STAGE_ORDER
    }
    batch_options = {"Todos os batches": None} | {
        f"{row['created_at']} | {STAGE_LABELS.get(row['phase'], row['phase'])} | {row['batch_id']}": row["batch_id"]
        for row in batches
    }
    predictor_names = sorted({item.predictor_name for item in repo.list_pool_predictions()})
    model_options = {"Todos os modelos": None} | {name: name for name in predictor_names}
    f1, f2, f3 = st.columns(3)
    with f1:
        selected_round_label = st.selectbox("Filtro de rodada", list(round_options.keys()))
        selected_round = round_options[selected_round_label]
    with f2:
        selected_phase_label = st.selectbox("Filtro de fase", list(phase_options.keys()))
        selected_phase = phase_options[selected_phase_label]
    with f3:
        selected_batch_label = st.selectbox("Filtro de batch", list(batch_options.keys()))
        selected_batch = batch_options[selected_batch_label]
    f4, f5, f6 = st.columns(3)
    with f4:
        selected_model_label = st.selectbox("Filtro de modelo", list(model_options.keys()))
        selected_model = model_options[selected_model_label]
    with f5:
        final_only = st.checkbox("Somente palavra final", value=True)
    with f6:
        include_combo = st.checkbox("Incluir combo", value=True)
    standings = leaderboard(repo)
    if not standings:
        st.info("Ainda nao ha palpites pontuados.")
    else:
        cols = st.columns(min(4, len(standings)))
        for index, standing in enumerate(standings[:8], 1):
            color = [GOLD, "#b9c7c4", "#d98a5f", ACCENT][min(index - 1, 3)]
            with cols[(index - 1) % len(cols)]:
                st.markdown(
                    f"""<div class="cm-podium" style="border-top-color:{color}">
<span>#{index}</span><b>{escape(standing.predictor_name)}</b>
<strong>{standing.total_points}</strong><small>{standing.predictions} palpites | Brier {standing.mean_brier:.3f}</small>
</div>""",
                    unsafe_allow_html=True,
                )
    st.markdown("### Historico pontuado")
    _history_table(
        repo,
        round_id=selected_round,
        batch_id=selected_batch,
        phase=selected_phase,
        model_id=selected_model,
        final_only=final_only,
        include_combo=include_combo,
    )
    st.markdown("### Acuracidade por fase/modelo")
    _phase_accuracy_table(
        repo,
        round_id=selected_round,
        batch_id=selected_batch,
        phase=selected_phase,
        model_id=selected_model,
        final_only=final_only,
        include_combo=include_combo,
    )
    st.markdown("### Rodadas LLM")
    _rounds_table(repo)
    st.markdown("### Batches por fase")
    _batches_table(repo)
    with st.expander("Payloads completos das LLMs"):
        payloads = repo.list_pool_prediction_payloads()
        if payloads:
            st.dataframe(pd.DataFrame(payloads), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhum payload completo salvo ainda.")


def _compact_match(match: Match) -> None:
    st.markdown(
        f"""<div class="cm-row">
<b>{escape(_stage(match))}</b><span>{escape(_match_label(match))}</span>
</div>""",
        unsafe_allow_html=True,
    )


def _match_header(match: Match) -> None:
    col1, mid, col2 = st.columns([1, 1.2, 1])
    with col1:
        st.image(flag_url(match.home_team_id), width=54)
        st.markdown(f"**{team_label(match.home_team_id)}**")
    with mid:
        st.markdown(f"<div class='cm-versus'>{escape(_stage(match))}<b>{escape(_date(match))}</b><span>vs</span></div>", unsafe_allow_html=True)
    with col2:
        st.image(flag_url(match.away_team_id), width=54)
        st.markdown(f"**{team_label(match.away_team_id)}**")


def _match_operational_card(repo: DuckDBRepository, match: Match) -> None:
    predictions = [p for p in repo.list_pool_predictions() if p.match_id == match.match_id]
    with st.container(border=True):
        top = st.columns([1.4, 1, 1])
        with top[0]:
            _match_header(match)
        with top[1]:
            st.metric("Palpites travados", len(predictions))
            st.caption(_stage(match))
        with top[2]:
            if st.button("Gerar ML", key=f"ml-{match.match_id}", use_container_width=True):
                generated = lock_match_predictions(repo, match, [PoissonPredictor(), EloPredictor()])
                st.success(f"{len(generated)} palpites ML travados.")
                st.rerun()
        if predictions:
            _prediction_strip(predictions)


def _prediction_strip(predictions: list[PoolPrediction]) -> None:
    rows = [
        {
            "Modelo": p.predictor_name,
            "Placar": f"{p.predicted_home_goals}-{p.predicted_away_goals}",
            "Casa": f"{p.prob_home:.1%}",
            "Empate": f"{p.prob_draw:.1%}",
            "Fora": f"{p.prob_away:.1%}",
        }
        for p in predictions
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _latest_consensus_labels(repo: DuckDBRepository) -> dict[str, str]:
    labels: dict[str, str] = {}
    best_scores: dict[str, tuple[float, datetime]] = {}
    for row in repo.list_llm_model_consensus():
        match_id = str(row["match_id"])
        score = float(row.get("coherence_score") or 0)
        created_at = row.get("created_at")
        created = created_at if isinstance(created_at, datetime) else datetime.min
        current = best_scores.get(match_id)
        if current and (score, created) <= current:
            continue
        best_scores[match_id] = (score, created)
        probs = {
            "home": float(row.get("prob_home") or 0),
            "draw": float(row.get("prob_draw") or 0),
            "away": float(row.get("prob_away") or 0),
        }
        confidence = max(probs.values()) if probs else 0
        labels[match_id] = (
            f"{row['predicted_home_goals']}-{row['predicted_away_goals']} "
            f"{confidence:.0%} | {row['model_id']}"
        )
    return labels


def _match_context_panel(repo: DuckDBRepository, match: Match) -> None:
    _match_header(match)
    home_stats = team_summary(match.home_team_id)
    away_stats = team_summary(match.away_team_id)
    cols = st.columns(4)
    metrics = [
        ("Gols", "goals"),
        ("xG", "xg"),
        ("Finalizacoes", "shots"),
        ("Gols sofridos", "goals_conceded"),
    ]
    for idx, (label, key) in enumerate(metrics):
        with cols[idx]:
            st.metric(label, f"{home_stats[key]:.1f}", f"{away_stats[key]:.1f} adversario")
    left, right = st.columns(2)
    with left:
        _team_stats_panel(match.home_team_id)
    with right:
        _team_stats_panel(match.away_team_id)


def _team_stats_panel(team_id: str) -> None:
    stats = team_summary(team_id)
    players = top_players(team_id, limit=26)
    st.markdown(f"### {team_label(team_id)}")
    st.image(stats["flag_url"], width=46)
    rows = [
        {"Metrica": "Gols", "Valor": stats["goals"]},
        {"Metrica": "xG", "Valor": stats["xg"]},
        {"Metrica": "Finalizacoes", "Valor": stats["shots"]},
        {"Metrica": "Posse", "Valor": stats["possession"]},
        {"Metrica": "Passes", "Valor": stats["passes"]},
        {"Metrica": "Gols sofridos", "Valor": stats["goals_conceded"]},
        {"Metrica": "Sprints", "Valor": stats["sprints"]},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if players:
        st.markdown("Jogadores-chave")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Foto": p["image_url"],
                        "Jogador": p["name"],
                        "Pos": p["position"],
                        "Gols": p["goals"],
                        "Assist": p["assists"],
                        "Min": p["minutes"],
                    }
                    for p in players
                ]
            ),
            use_container_width=True,
            hide_index=True,
            column_config={"Foto": st.column_config.ImageColumn(width="small")},
        )


def _result_form(repo: DuckDBRepository, match: Match) -> None:
    _match_header(match)
    with st.form(f"result-{match.match_id}"):
        c1, c2 = st.columns(2)
        home_score = c1.number_input(team_label(match.home_team_id), min_value=0, max_value=20, value=0)
        away_score = c2.number_input(team_label(match.away_team_id), min_value=0, max_value=20, value=0)
        submitted = st.form_submit_button("Salvar resultado e pontuar", use_container_width=True)
    if submitted:
        repo._con.execute(
            "UPDATE matches SET home_score=?, away_score=?, status=?, available_at=? WHERE match_id=?",
            [int(home_score), int(away_score), str(MatchStatus.finished), datetime.now(UTC), match.match_id],
        )
        repo.upsert_pool_result(
            PoolResult(
                match_id=match.match_id,
                home_score=int(home_score),
                away_score=int(away_score),
                recorded_at=datetime.now(UTC),
            )
        )
        st.success("Resultado salvo. Ranking atualizado.")
        st.rerun()


def _run_llm_pick(repo: DuckDBRepository, match: Match, model_id: str, temperature: float) -> None:
    result = BolaoLLMAgent(_lm_client(), model_id, temperature=temperature).run(repo, match)
    if result.pick is None:
        _save_llm_payload(repo, match, result)
        st.error(result.error or "Resposta invalida.")
        return
    locked = _lock_pick(repo, match, result.predictor_name, result.pick, result.model_dump())
    st.success("Palpite da LLM travado." if locked else "Este modelo ja tinha palpite travado.")
    st.json(result.pick.model_dump())


def _phase_runner_panel(repo: DuckDBRepository, model_infos: list[LocalModelInfo]) -> None:
    st.markdown("### Processar estatisticas das IAs por fase")
    phase_choices = {
        STAGE_LABELS[key]: key
        for key in KNOCKOUT_PHASES
    }
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        phase_label = st.selectbox("Fase", list(phase_choices.keys()), key="phase-runner-stage")
    phase = phase_choices[phase_label]
    with c2:
        include_finished = st.checkbox("Incluir finalizados", value=False)
    with c3:
        samples = st.number_input("Amostras por modelo", min_value=1, max_value=3, value=1)

    phase_matches = [match for match in _matches(repo) if str(match.stage) == phase]
    if not include_finished:
        phase_matches = [match for match in phase_matches if match.status is MatchStatus.scheduled]
    phase_matches.sort(key=lambda item: (item.match_date, item.match_id))
    if not phase_matches:
        st.caption("Nao ha partidas elegiveis para esta fase.")
        return

    label_to_match = {_match_label(match): match for match in phase_matches}
    selected_labels = st.multiselect(
        "Partidas da fase",
        list(label_to_match.keys()),
        default=list(label_to_match.keys()),
        key="phase-runner-matches",
    )
    selected_matches = [label_to_match[label] for label in selected_labels]
    runnable = [info for info in model_infos if info.participates or info.model_class == "heavy"]
    st.caption(
        f"{len(selected_matches)} jogos selecionados | "
        f"{len(runnable)} modelos de chat compativeis | embeddings/OCR ficam fora."
    )
    if st.button("Processar fase com LLMs", use_container_width=True):
        _run_llm_phase(repo, selected_matches, runnable, phase=phase, samples_per_model=int(samples))


def _run_llm_phase(
    repo: DuckDBRepository,
    matches: list[Match],
    model_infos: list[LocalModelInfo],
    *,
    phase: str,
    samples_per_model: int,
) -> None:
    if not matches:
        st.warning("Nenhuma partida selecionada.")
        return
    if not model_infos:
        st.warning("Nenhum modelo participante selecionado.")
        return
    batch_id = f"llmbatch-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    repo.insert_llm_phase_batch(
        batch_id,
        phase,
        datetime.now(UTC),
        "running",
        len(matches),
        [info.model_id for info in model_infos],
    )
    failures = 0
    phase_progress = st.progress(0, text=f"Iniciando batch {batch_id}")
    for index, match in enumerate(matches, 1):
        phase_progress.progress(
            (index - 1) / len(matches),
            text=f"{index}/{len(matches)}: {_match_label(match)}",
        )
        try:
            _run_llm_pool(
                repo,
                match,
                model_infos,
                batch_id=batch_id,
                phase=phase,
                samples_per_model=samples_per_model,
            )
        except Exception as exc:
            failures += 1
            st.error(f"Falha em {_match_label(match)}: {exc}")
    status = "completed" if failures == 0 else "completed_with_errors"
    repo.update_llm_phase_batch_status(batch_id, status)
    phase_progress.progress(1.0, text=f"Batch {batch_id} concluido.")
    st.success(f"Batch {batch_id}: {len(matches) - failures}/{len(matches)} jogos processados.")


def _run_llm_pool(
    repo: DuckDBRepository,
    match: Match,
    model_infos: list[LocalModelInfo],
    *,
    batch_id: str | None = None,
    phase: str | None = None,
    samples_per_model: int = 1,
) -> None:
    if not model_infos:
        st.warning("Nenhum modelo participante selecionado.")
        return
    client = _lm_client()
    rid = new_round_id()
    repo.insert_llm_pool_round(
        rid,
        match.match_id,
        datetime.now(UTC),
        "running",
        samples_per_model,
        [info.model_id for info in model_infos],
        batch_id=batch_id,
        phase=phase,
    )
    consensuses: list[LLMModelConsensus] = []
    progress = st.progress(0, text="Chamando modelos locais...")
    for index, info in enumerate(model_infos, 1):
        progress.progress((index - 1) / len(model_infos), text=f"{info.model_id}: {samples_per_model} amostras")
        runs = run_model_sample_results(
            client,
            repo,
            match,
            info.model_id,
            samples=samples_per_model,
            temperature=0.2,
        )
        for sample_index, result in enumerate(runs, 1):
            _save_llm_run(repo, match, rid, result, sample_index)
        consensus = build_model_consensus_from_runs(
            match,
            info.model_id,
            rid,
            runs,
            total_samples=samples_per_model,
        )
        if consensus is None:
            failed_result = LLMRunResult(
                model_id=info.model_id,
                predictor_name=f"llm:{info.model_id}:round:{rid}",
                status="invalid",
                error="nenhuma amostra valida",
            )
            _save_llm_payload(repo, match, failed_result)
        else:
            _save_consensus(repo, match, consensus)
            consensus.runs = [
                run.model_copy(update={"locked": False}) for run in consensus.runs
            ]
            _lock_pick(
                repo,
                match,
                consensus.predictor_name,
                consensus.pick,
                _consensus_payload(consensus),
            )
            consensuses.append(consensus)
        client.unload(info.model_id)
    progress.progress(1.0, text="Rodada concluida.")

    valid_picks = [consensus.pick for consensus in consensuses]
    combo = build_combo_pick(match, valid_picks)
    if combo is not None:
        combo_predictor = f"combo:llm_pool:round:{rid}"
        _lock_pick(
            repo,
            match,
            combo_predictor,
            combo,
            {
                "status": "valid",
                "source": "combo",
                "round_id": rid,
                "models": [consensus.model_id for consensus in consensuses],
                "pick": combo.model_dump(),
            },
        )
    repo.update_llm_pool_round_status(rid, "completed" if consensuses else "failed")

    rows = [
        {
            "Modelo": consensus.model_id,
            "Validas": f"{consensus.valid_samples}/{consensus.total_samples}",
            "Coerencia": round(consensus.coherence_score, 3),
            "Placar": f"{consensus.pick.predicted_home_goals}-{consensus.pick.predicted_away_goals}",
            "Casa": f"{consensus.pick.prob_home:.1%}",
            "Empate": f"{consensus.pick.prob_draw:.1%}",
            "Fora": f"{consensus.pick.prob_away:.1%}",
            "1o gol": consensus.pick.first_goal_scorer or "-",
        }
        for consensus in consensuses
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.success(
        f"Rodada {rid}: {len(valid_picks)} palavras finais. "
        f"Combo {'criado' if combo else 'nao criado'}."
    )


def _lock_pick(
    repo: DuckDBRepository,
    match: Match,
    predictor_name: str,
    pick: LLMMatchPick,
    payload: dict[str, Any],
) -> bool:
    prediction_id = f"{predictor_name}:{match.match_id}"
    locked_at = datetime.now(UTC)
    if repo.pool_prediction_exists(prediction_id):
        repo.upsert_pool_prediction_payload(
            prediction_id,
            predictor_name,
            match.match_id,
            payload | {"locked": False, "reason": "prediction_exists"},
            locked_at,
        )
        return False
    data = pick.as_pool_prediction()
    repo.insert_pool_prediction(
        PoolPrediction(
            prediction_id=prediction_id,
            predictor_name=predictor_name,
            match_id=match.match_id,
            snapshot_id=repo.latest_snapshot_id() or "adhoc",
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            prob_home=data.prob_home,
            prob_draw=data.prob_draw,
            prob_away=data.prob_away,
            predicted_home_goals=data.predicted_home_goals,
            predicted_away_goals=data.predicted_away_goals,
            locked_at=locked_at,
        )
    )
    repo.upsert_pool_prediction_payload(
        prediction_id,
        predictor_name,
        match.match_id,
        payload | {"locked": True},
        locked_at,
    )
    return True


def _save_llm_payload(repo: DuckDBRepository, match: Match, result: LLMRunResult) -> None:
    created_at = datetime.now(UTC)
    prediction_id = f"{result.predictor_name}:{match.match_id}:invalid"
    repo.upsert_pool_prediction_payload(
        prediction_id,
        result.predictor_name,
        match.match_id,
        result.model_dump(),
        created_at,
    )


def _save_llm_run(
    repo: DuckDBRepository,
    match: Match,
    round_id: str,
    result: LLMRunResult,
    sample_index: int,
) -> None:
    repo.insert_llm_model_run(
        run_id=f"{round_id}:{result.model_id}:{sample_index}",
        round_id=round_id,
        match_id=match.match_id,
        model_id=result.model_id,
        predictor_name=result.predictor_name,
        sample_index=sample_index,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        latency_ms=result.latency_ms,
        raw_response=result.raw_response,
        valid=result.pick is not None,
        error=result.error,
        attempts=result.attempts,
        pick=result.pick.model_dump() if result.pick else None,
        created_at=datetime.now(UTC),
    )


def _save_consensus(
    repo: DuckDBRepository,
    match: Match,
    consensus: LLMModelConsensus,
) -> None:
    pick = consensus.pick
    repo.upsert_llm_model_consensus(
        consensus_id=f"{consensus.round_id}:{consensus.model_id}",
        round_id=consensus.round_id,
        match_id=match.match_id,
        model_id=consensus.model_id,
        predictor_name=consensus.predictor_name,
        valid_samples=consensus.valid_samples,
        total_samples=consensus.total_samples,
        prob_home=pick.prob_home,
        prob_draw=pick.prob_draw,
        prob_away=pick.prob_away,
        predicted_home_goals=pick.predicted_home_goals,
        predicted_away_goals=pick.predicted_away_goals,
        winner=pick.winner,
        first_goal_scorer=pick.first_goal_scorer,
        coherence_score=consensus.coherence_score,
        coherence_notes=consensus.coherence_notes,
        payload=_consensus_payload(consensus),
        created_at=datetime.now(UTC),
    )


def _consensus_payload(consensus: LLMModelConsensus) -> dict[str, Any]:
    return {
        "status": "valid",
        "round_id": consensus.round_id,
        "model_id": consensus.model_id,
        "valid_samples": consensus.valid_samples,
        "total_samples": consensus.total_samples,
        "coherence_score": consensus.coherence_score,
        "coherence_notes": consensus.coherence_notes,
        "runs": [run.model_dump() for run in consensus.runs],
        "pick": consensus.pick.model_dump(),
    }


def _history_table(
    repo: DuckDBRepository,
    *,
    round_id: str | None = None,
    batch_id: str | None = None,
    phase: str | None = None,
    model_id: str | None = None,
    final_only: bool = False,
    include_combo: bool = True,
) -> None:
    results = {item.match_id: item for item in repo.list_pool_results()}
    matches = {item.match_id: item for item in repo.list_matches(limit=800)}
    batch_round_ids = _round_ids_for_batch(repo, batch_id)
    rows: list[dict[str, Any]] = []
    for prediction in repo.list_pool_predictions():
        match = matches.get(prediction.match_id)
        if not _prediction_passes_filters(
            prediction,
            match,
            round_id=round_id,
            batch_round_ids=batch_round_ids,
            phase=phase,
            model_id=model_id,
            final_only=final_only,
            include_combo=include_combo,
        ):
            continue
        result = results.get(prediction.match_id)
        if result is None:
            continue
        actual = outcome(result.home_score, result.away_score)
        points = bolao_points(
            prediction.predicted_home_goals,
            prediction.predicted_away_goals,
            result.home_score,
            result.away_score,
        )
        rows.append(
            {
                "Partida": _match_label(match) if match else prediction.match_id,
                "Modelo": prediction.predictor_name,
                "Palpite": f"{prediction.predicted_home_goals}-{prediction.predicted_away_goals}",
                "Real": f"{result.home_score}-{result.away_score}",
                "Pts": points,
                "Brier": round(
                    brier_score(prediction.prob_home, prediction.prob_draw, prediction.prob_away, actual),
                    4,
                ),
            }
        )
    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values(["Pts", "Brier"], ascending=[False, True]), use_container_width=True, hide_index=True)
    else:
        st.caption("Nenhum palpite com resultado real ainda.")


def _phase_accuracy_table(
    repo: DuckDBRepository,
    *,
    round_id: str | None = None,
    batch_id: str | None = None,
    phase: str | None = None,
    model_id: str | None = None,
    final_only: bool = False,
    include_combo: bool = True,
) -> None:
    results = {item.match_id: item for item in repo.list_pool_results()}
    matches = {item.match_id: item for item in repo.list_matches(limit=800)}
    batch_round_ids = _round_ids_for_batch(repo, batch_id)
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for prediction in repo.list_pool_predictions():
        match = matches.get(prediction.match_id)
        if not _prediction_passes_filters(
            prediction,
            match,
            round_id=round_id,
            batch_round_ids=batch_round_ids,
            phase=phase,
            model_id=model_id,
            final_only=final_only,
            include_combo=include_combo,
        ):
            continue
        result = results.get(prediction.match_id)
        if result is None or match is None:
            continue
        actual = outcome(result.home_score, result.away_score)
        predicted = outcome(prediction.predicted_home_goals, prediction.predicted_away_goals)
        key = (prediction.predictor_name, str(match.stage))
        item = grouped.setdefault(
            key,
            {
                "Modelo": prediction.predictor_name,
                "Fase": STAGE_LABELS.get(str(match.stage), str(match.stage)),
                "Jogos": 0,
                "Pontos": 0,
                "Vencedor": 0,
                "Placar exato": 0,
                "Brier soma": 0.0,
                "Erro gols": 0.0,
            },
        )
        item["Jogos"] += 1
        item["Pontos"] += bolao_points(
            prediction.predicted_home_goals,
            prediction.predicted_away_goals,
            result.home_score,
            result.away_score,
        )
        item["Vencedor"] += int(predicted == actual)
        item["Placar exato"] += int(
            prediction.predicted_home_goals == result.home_score
            and prediction.predicted_away_goals == result.away_score
        )
        item["Brier soma"] += brier_score(
            prediction.prob_home,
            prediction.prob_draw,
            prediction.prob_away,
            actual,
        )
        item["Erro gols"] += abs(prediction.predicted_home_goals - result.home_score) + abs(
            prediction.predicted_away_goals - result.away_score
        )
    rows = []
    for item in grouped.values():
        jogos = int(item["Jogos"])
        rows.append(
            {
                "Modelo": item["Modelo"],
                "Fase": item["Fase"],
                "Jogos": jogos,
                "Pontos": item["Pontos"],
                "Pts/jogo": round(item["Pontos"] / jogos, 2),
                "Vencedor": f"{item['Vencedor'] / jogos:.1%}",
                "Placar exato": f"{item['Placar exato'] / jogos:.1%}",
                "Brier": round(item["Brier soma"] / jogos, 4),
                "Erro gols": round(item["Erro gols"] / jogos, 2),
            }
        )
    if rows:
        st.dataframe(
            pd.DataFrame(rows).sort_values(["Pontos", "Brier"], ascending=[False, True]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Nenhuma metrica calculavel com os filtros atuais.")


def _round_ids_for_batch(repo: DuckDBRepository, batch_id: str | None) -> set[str]:
    if not batch_id:
        return set()
    return {row["round_id"] for row in repo.list_llm_pool_rounds(batch_id=batch_id)}


def _prediction_passes_filters(
    prediction: PoolPrediction,
    match: Match | None,
    *,
    round_id: str | None,
    batch_round_ids: set[str],
    phase: str | None,
    model_id: str | None,
    final_only: bool,
    include_combo: bool,
) -> bool:
    if round_id and f":round:{round_id}" not in prediction.predictor_name:
        return False
    if batch_round_ids and not any(
        f":round:{rid}" in prediction.predictor_name for rid in batch_round_ids
    ):
        return False
    if phase and (match is None or str(match.stage) != phase):
        return False
    if model_id and prediction.predictor_name != model_id:
        return False
    if not include_combo and prediction.predictor_name.startswith("combo:"):
        return False
    return not final_only or _is_final_llm_prediction(prediction.predictor_name)


def _is_final_llm_prediction(predictor_name: str) -> bool:
    return (
        (predictor_name.startswith("llm:") and ":round:" in predictor_name)
        or predictor_name.startswith("combo:llm_pool:round:")
    )


def _rounds_table(repo: DuckDBRepository) -> None:
    rounds = repo.list_llm_pool_rounds()
    if not rounds:
        st.caption("Nenhuma rodada LLM registrada.")
        return
    consensus = repo.list_llm_model_consensus()
    by_round: dict[str, list[dict[str, Any]]] = {}
    for row in consensus:
        by_round.setdefault(row["round_id"], []).append(row)
    rows = []
    for row in rounds:
        items = by_round.get(row["round_id"], [])
        rows.append(
            {
                "Rodada": row["round_id"],
                "Partida": row["match_id"],
                "Batch": row.get("batch_id") or "-",
                "Fase": STAGE_LABELS.get(str(row.get("phase") or ""), row.get("phase") or "-"),
                "Status": row["status"],
                "Amostras": row["samples_per_model"],
                "Modelos": len(row["selected_models"]),
                "Consensos": len(items),
                "Coerencia media": _round_or_dash(
                    sum(item["coherence_score"] for item in items) / len(items) if items else None,
                    3,
                ),
                "Criada em": row["created_at"],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _batches_table(repo: DuckDBRepository) -> None:
    batches = repo.list_llm_phase_batches()
    if not batches:
        st.caption("Nenhum batch por fase registrado.")
        return
    rows = [
        {
            "Batch": row["batch_id"],
            "Fase": STAGE_LABELS.get(row["phase"], row["phase"]),
            "Status": row["status"],
            "Jogos": row["match_count"],
            "Modelos": len(row["selected_models"]),
            "Criado em": row["created_at"],
        }
        for row in batches
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _pct(part: object, total: object) -> str:
    total_num = float(total or 0)
    if total_num <= 0:
        return "-"
    return f"{float(part or 0) / total_num:.1%}"


def _round_or_dash(value: object, digits: int = 0) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return str(round(number, digits))


def main() -> None:
    st.set_page_config(
        page_title="CopaMind 2026",
        page_icon="docs/assets/icon.png" if os.path.exists("docs/assets/icon.png") else None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject()
    page = _sidebar()
    if page == "Home":
        render_home()
    elif page == "Proximos Jogos":
        render_proximos_jogos()
    elif page == "Bolao das LLMs":
        render_bolao_llms()
    elif page == "Modelos LM Studio":
        render_modelos_lmstudio()
    elif page == "Dados FIFA":
        render_dados_fifa()
    elif page == "Ranking":
        render_ranking()


if __name__ == "__main__":
    main()
