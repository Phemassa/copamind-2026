# CHANGELOG.md

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- **Épico E10 (Evolução 24 GB, core):** perfis de hardware (`copamind.llm.hardware`: `HardwareProfile`, `load_hardware_profiles`, `detect_vram_gb`, `suggest_profile`); `copamind doctor` detecta a VRAM (nvidia-smi) e sugere o perfil; sequencial permanece o default, concorrência é opt-in do perfil 24gb. 160 testes verdes.
- **Ingestão real (OpenFootball):** conector `worldcup.json` (`copamind.data.connectors.openfootball`) tolerante a variações de formato; serviço `ingest_worldcup` e comando `copamind ingest worldcup <path>`. `confederation` agora é opcional (fontes nem sempre fornecem).
- **RAG — reranker:** protocolo `Reranker` + `LexicalReranker` (baseline offline), plugável no `HybridRetriever` (cross-encoder bge-reranker pode substituir).
- **RAG — QdrantStore:** backend vetorial real (import lazy do `qdrant-client`, extra `rag`).
- **Chat SSE:** `SequentialOrchestrator.run_events` (eventos por etapa) e rota `POST /chat/stream` (Server-Sent Events).
- **Bolão com LLMs + bracket:** `LLMPredictor` no Bolão de IAs; `stage_probabilities_view` e visualização "caminho até o título" no dashboard. 156 testes verdes.
- **Épico E9 (Conteúdo & Publicação, core):** README com badges e seção de recursos; `CONTRIBUTING.md`, `SECURITY.md`, `MODEL_CARD.md`; templates de issue (bug/feature/data source) e PR; gerador de cards bilíngues (`copamind content ranking|match`). 147 testes verdes.
- **Épico E8b (Chat na UI + calibração):** página de chat no dashboard com 3 boxes (analista/challenger/auditor) + consenso, via orquestrador de LLMs (cliente LM Studio; resiliente quando indisponível); curva de calibração (reliability) por preditor; helpers testáveis `chat_view` (cliente injectável) e `calibration_view`; i18n do chat. 145 testes verdes.
- **Épico E6 (MCP `copamind-mcp`, core):** camada de ferramentas testável (dados, predição, ensemble, simulação, RAG, calibração, bolão) separando read-only (`READ_ONLY_TOOLS`) de escrita (`WRITE_TOOLS`); servidor FastMCP com import lazy do pacote `mcp`; comando `copamind mcp serve`; extra `mcp`. 143 testes verdes.
- **Épico E3b (Ensemble + Calibração):** blend de probabilidades Elo+Poisson (`blend`, `blend_named`, `fit_two_model_weights` por grade Brier); calibração isotônica via PAV (`IsotonicCalibrator`, `CalibratedTriples`); métricas Brier/Log-Loss/ECE + curva de confiabilidade; relatório de calibração sobre os dados do bolão; serviço `ensemble_match`; rotas `POST /predictions/ensemble` e `GET /pool/calibration`. CatBoost/XGBoost/SHAP adiados (dataset sintético pequeno). 134 testes verdes.
- **Épico E5 (RAG, core):** `RagChunk` com metadados/linhagem; embeddings (`FakeEmbedder` offline, `OllamaEmbedder`/bge-m3 real); `InMemoryVectorStore` (Qdrant opcional via extra `rag`); `HybridRetriever` (vetorial + léxico + recência + qualidade + verificação + entidade); proteção anti prompt-injection (`build_grounded_context`); indexação de relatos; rotas `/rag/index`, `/rag/search`, `/rag/sources`; comando `copamind rag index`. 122 testes verdes.
- **Épico E2 (User Reports & Memória):** schema `UserReport` versionado (histórico preservado, tombstone na exclusão); tabela `user_reports`; extratores (`RuleBasedExtractor` offline + `LLMExtractor`); serviço de criar/corrigir/verificar/excluir; rotas REST `/user-reports` (POST/GET/PATCH/DELETE/verify); comando `copamind ingest user-report`; `source_type=user_input`, nunca promovido ao treino. 111 testes verdes.
- **Épico E7 (Orquestração de LLMs + Benchmark, core):** clientes LM Studio/Ollama + `FakeLLMClient`; contratos de saída (`AnalystResponse`, `AuditorResponse`, `ConsensusResponse`) com grounding e `response_language`; orquestrador sequencial analista→challenger→auditor→consenso com unload e falha isolada; pacote de evidências a partir dos modelos estatísticos; harness de benchmark (schema/groundedness/latência/tokens-s); loader de perfis (`models.yaml`); comando `copamind llm benchmark`. 101 testes verdes.
- **Épico E11 (Bolão de IAs Locais):** preditores plugáveis (`poisson`, `elo`; LLMs no E7); palpites imutáveis travados por snapshot (`pool_predictions`), resultados (`pool_results`); pontuação de bolão (placar exato/resultado) + Brier; leaderboard por preditor; backtest anti-leakage (as_of por partida); rotas `POST /pool/backtest` e `GET /pool/leaderboard`; comando `copamind pool run`; aba Bolão no dashboard. 91 testes verdes.
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
