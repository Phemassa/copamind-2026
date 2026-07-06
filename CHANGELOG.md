# CHANGELOG.md

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- **Épico E8a (Dashboard Streamlit, bilíngue EN/PT-BR):** i18n (`copamind.ui.i18n`), helpers testáveis (`copamind.ui.dashboard`), app Streamlit (`apps/streamlit/app.py`) com visão geral, chances de título, análise de seleção e previsão de partida; comando `copamind ui serve`; extra `ui` (streamlit, plotly). 79 testes verdes.
- **Épico E4b (Simulação Monte Carlo):** motor de torneio configurável (fase de grupos turno único + mata-mata de eliminação simples com pênaltis), determinístico por seed, pré-amostragem vetorizada (NumPy); probabilidades de classificação/fase/título; serviço `run_simulation`; rota `POST /simulations`; comando `copamind simulate`. 70 testes verdes.
- **Épico E4 (Poisson / Dixon-Coles):** modelo de gols com forças de ataque/defesa (estimativa fechada, determinística, sem SciPy), matriz de placares, correção de Dixon-Coles para baixos placares, probabilidades 1x2 (soma ≈ 1), over 2.5 e placar mais provável; schema `Prediction` + tabela `predictions` + persistência; serviço `predict_match`; rota `POST /predictions/match`; comando `copamind train poisson`. 60 testes verdes.
- **Épico E3a (Elo + forma recente):** sistema de rating Elo determinístico (mando, importância, multiplicador por diferença de gols, histórico, `win_probability`); features de forma por janelas 5/10/15 com decaimento temporal opcional; serviço `analyze_team` (Elo + forma sem leakage); rota `GET /teams/{id}/form`; comando `copamind train elo`; método `list_finished_matches` (cronológico, anti-leakage). 47 testes verdes.
- **Épico E1 (Dados & Ingestão) concluído:** schemas Pydantic (Team, Coach, Player, Match, Snapshot) com linhagem; repositório DuckDB idempotente + CRUD; importadores JSON/CSV com validação e deduplicação; validação tabular Pandera; dataset sintético (`scripts/download_sample_data.py`); CLI `copamind ingest sample|file`; rotas `GET /teams`, `/teams/{id}`, `/teams/{id}/last-matches`, `/matches`; filtro anti-leakage `as_of` em `get_last_matches`. 32 testes verdes.
- **Épico E0 (Fundação) concluído:** pacote `src/copamind`, configuração (`pydantic-settings`), logging estruturado (`structlog`), API FastAPI com `/health` e `/ready`, CLI Typer com `copamind doctor`/`version`/`api serve`, Docker Compose do Qdrant, pre-commit, CI (GitHub Actions), README bilíngue-ready, LICENSE MIT. Ruff/mypy/pytest verdes (10 testes).
- Documento de planejamento consolidado (`MASTER_PLAN` §37 — Addendum v2).
- Backlog em épicos/histórias/tasks (`TASKS.md`, épicos E0–E11).
- Registro de decisões arquiteturais (`DECISIONS.md`, ADR-0001 a ADR-0013).
- Roadmap por marcos orientado a engajamento (`ROADMAP.md`).
- Épico **E10 — Evolução para servidor 24 GB VRAM** (perfis de hardware, roster 27–32B, execução concorrente opt-in, QLoRA do auditor).
- Épico **E11 — Bolão de IAs Locais** (palpites imutáveis por snapshot, scoring, leaderboard, cards).
- Roster de LLMs locais para 8 GB e diretrizes de embeddings/reranker (bge-m3, bge-reranker-v2-m3).
- Internacionalização EN/PT-BR como requisito de UI; campo `response_language` no contrato de resposta dos LLMs.
- Machine learning ampliado: SHAP, validação walk-forward, stacking com pesos aprendidos, incerteza, detecção de drift.

### Alterado
- Reordenação das fases para priorizar um slice vertical de engajamento (dados → Elo/Poisson → simulação → dashboard/bracket/cards → bolão).
- Stack de UI: Streamlit (MVP) + Reflex (demo pública); orquestração com Pydantic AI/LangGraph.

### Notas
- Pendência: confirmar specs atuais de Gemma 4 / Qwen3 / Phi-4 antes de fixar o roster final.
