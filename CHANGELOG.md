# CHANGELOG.md

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
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
