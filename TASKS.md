# CopaMind 2026 — Backlog (Épicos · Histórias · Tasks)

> Convenção: marque `[x]` ao concluir. Cada task só está "pronta" conforme a **Definição de Pronto** (MASTER_PLAN §31).
> Ordem operacional recomendada (slice vertical para engajamento — ver MASTER_PLAN §37.2):
> **E0 → E1 → E3a → E4 → E4b → E8a → E11 → E2 → E5 → E6 → E7 → E3b → E8b → E9**, com **E10** habilitável quando houver o servidor 24 GB.

---

## E0 — Fundação & DevEx ✅
Objetivo: repositório executável, com qualidade automatizada desde o início.

### H0.1 — Scaffold do repositório
- [x] `pyproject.toml` (Python 3.12, layout `src/`), pacote `src/copamind`
- [x] Ruff + mypy + pytest + pytest-cov + pre-commit configurados
- [x] GitHub Actions: lint, type-check, testes, `pip-audit`, `bandit`
- [x] `.env.example`, `config/*.example.yaml`, `logging.yaml`
- [x] `.gitignore` (inclui `data/user_input/` e artefatos locais)

### H0.2 — Esqueleto executável
- [x] FastAPI com `/health` e `/ready`
- [x] Typer CLI + `copamind doctor` (Python, DuckDB, Qdrant, LM Studio, Ollama, VRAM, disco, configs)
- [x] `docker/compose.yaml` sobe Qdrant

**Aceite:** pytest/ruff/mypy verdes; `/health` responde; Qdrant sobe via Docker; README com instalação Windows/Linux; nenhum segredo versionado. ✅

---

## E1 — Dados & Ingestão ✅
Objetivo: modelo de dados, persistência e ingestão reproduzível com linhagem.

### H1.1 — Schemas & persistência
- [x] Schemas Pydantic v2: Team, Coach, Player, Match (+ enums), Snapshot
- [x] Repositório DuckDB + migrations idempotentes + CRUD mínimo
- [x] Camadas raw/bronze/silver/gold documentadas

### H1.2 — Ingestão
- [x] Importador CSV
- [x] Importador JSON
- [x] Validação (Pydantic por linha + Pandera tabular) + rejeição de schema inválido
- [x] Deduplicação (por id e por chave lógica) de entidades/partidas
- [x] Campos de linhagem: `source`, `collected_at`, `available_at`, `snapshot_id`
- [x] Dataset sintético/redistribuível + `download_sample_data.py`
- [x] Conector real OpenFootball `worldcup.json` (`copamind ingest worldcup`)

**Aceite:** importar partidas; listar seleções; consultar últimos jogos; rejeitar dados inválidos; origem e snapshot registrados; ingestão reproduzível. ✅

> Nota: Lineups, PlayerMatchStats e TeamMatchStats serão adicionados quando exigidos por E3/E4.

---

## E3 — Motor Preditivo (ML)
Objetivo: ML é o motor de probabilidades (o LLM nunca sobrescreve). Dividido em E3a (rápido) e E3b (avançado).

### E3a — Baseline rápido
#### H3.1 — Elo ✅
- [x] Rating com mando, importância e diferença de gols (decaimento temporal aplicado à forma)
- [x] Saídas: rating atual, probabilidade esperada, histórico
- [x] Reprodutível e independente da ordem de entrada
#### H3.2 — Forma recente ✅ (parcial)
- [x] Janelas 5/10/15 jogos (com decaimento temporal opcional)
- [ ] Janelas por dias (365/730) — futuro
- [ ] Ajuste por adversário (Elo, ranking, confederação, local) — E3b/feature engineering
- [x] Testes de leakage dedicados (`as_of`)

### E3b — Avançado
#### H3.3 — Poisson / Dixon-Coles ✅
- [x] Ataque/defesa, matriz de placares, 1x2, over/under, mata-mata
#### H3.4 — CatBoost
- [ ] Dataset temporal + pipeline + tuning Optuna (Brier/Log-Loss) + model registry
#### H3.5 — XGBoost / LightGBM
- [ ] Modelo adicional para diversidade de ensemble — futuro (requer dataset real)
#### H3.6 — Ensemble & calibração ✅
- [x] Blend de probabilidades (Elo + Poisson) com pesos configuráveis / aprendidos (grade Brier)
- [x] Calibração isotônica (PAV), curva de confiabilidade, Brier, Log-Loss, ECE
#### H3.7 — Explicabilidade & incerteza
- [ ] SHAP / feature importance — futuro (com CatBoost)
- [ ] Intervalos de incerteza (bootstrap / Monte Carlo) — futuro
#### H3.8 — Anti-vazamento temporal
- [x] Filtro `as_of` em Elo/Poisson/ensemble; testes de leakage (E3a)

**Aceite:** rating reproduzível; probabilidades somam ~1; backtest e métricas documentados; artefatos versionados; sem leakage.

---

## E4 — Simulação Monte Carlo ✅
Objetivo: simulador do torneio independente dos LLMs.

### H4.1 — Regras do torneio
- [x] Grupos, mata-mata, pênaltis, chaveamento, desempate (saldo/gols)
- [ ] Melhores terceiros, prorrogação explícita — futuro (config-driven)
### H4.2 — Motor Monte Carlo
- [x] Vetorização NumPy (pré-amostragem de gols), seed reproduzível, 10k+ simulações
### H4.3 — Saídas & persistência
- [x] Probabilidade por fase/título, classificação; API

**Aceite:** 10.000 simulações em segundos; resultados somam corretamente; testes de chaveamento; seed reproduzível. ✅

---

## E2 — User Reports & Memória ✅ (RAG na E5)
Objetivo: ingestão de texto livre do usuário com ciclo de vida controlado.

### H2.1 — Ingestão de texto livre
- [x] Endpoint POST + extração estruturada (regras; LLM opcional via `LLMExtractor`)
- [x] Detecção de entidades e tipo (match_result/injury/general)
### H2.2 — Ciclo de vida
- [x] Listar / editar / excluir (tombstone) / verificar
- [x] Versionamento (histórico preservado)
- [x] Marcação `source_type=user_input`, `verified=false`, `confidence`

**Aceite:** salvar/recuperar; corrigir (nova versão); impedir promoção automática ao treino; histórico preservado. ✅ (indexação RAG = E5)

---

## E5 — RAG ✅ (core)
Objetivo: recuperação híbrida segura, multilíngue e auditável.

### H5.1 — Indexação
- [x] Chunking + metadados completos (`RagChunk`)
- [x] Embeddings (FakeEmbedder offline; OllamaEmbedder/bge-m3 real) + store (InMemory; Qdrant opcional)
### H5.2 — Busca híbrida
- [x] Vetorial + léxico + filtros + recência/confiabilidade/verificação/entidade
- [x] Reranker plugável (`LexicalReranker`; cross-encoder bge-reranker como evolução)
- [x] `QdrantStore` (backend real, extra `rag`)
### H5.3 — Segurança
- [x] Contexto tratado como não confiável; anti prompt-injection; chunk_ids usados registrados
### H5.4 — Avaliação
- [ ] Dataset de eval (recall@k, MRR, groundedness) — futuro

**Aceite:** busca híbrida retorna docs esperados; injeção marcada; chunks usados registrados. ✅

---

## E6 — MCP (`copamind-mcp`) ✅ (core)
Objetivo: expor ferramentas locais ao agente com menor privilégio.

### H6.1 — Tools read-only
- [x] Dados (`list_teams`, `get_last_matches`, `get_head_to_head`, `get_team_form`, `get_data_freshness`)
- [x] Predição (`predict_match`, `ensemble_predict`, `run_tournament_simulation`)
- [x] RAG (`search_knowledge`), auditoria (`get_calibration`, `get_pool_leaderboard`)
### H6.2 — Tools de escrita
- [x] `add_user_report` / `verify_user_report` / `delete_user_report`, separadas (WRITE_TOOLS)
### H6.3 — Segurança
- [x] Read-only e write separadas; args validados; repo por chamada; import lazy do `mcp`

**Aceite:** agente consulta jogos/previsão/RAG; read-only e write separadas; servidor via `copamind mcp serve`. ✅

---

## E7 — Orquestração de LLMs + Benchmark ✅ (core)
Objetivo: execução sequencial com unload, consenso auditável e benchmark local.

### H7.1 — Cliente & perfis
- [x] Cliente LM Studio (OpenAI-compat) + Ollama + FakeLLMClient (testes)
- [x] `models.yaml` (perfis) + loader `load_model_specs`
- [x] Saída estruturada via JSON + validação Pydantic (contratos §15.4, `response_language`)
### H7.2 — Pipeline sequencial
- [x] analista → unload → challenger → unload → auditor → unload → consenso
- [x] Falha de um modelo não derruba a sessão
### H7.3 — Grounding & auditoria
- [x] Claims ligados a `evidence_id`; auditor com veredito por claim
### H7.4 — Benchmark harness (feature)
- [x] Métricas: aderência a schema, groundedness, latência, tokens/s, concordância com ML
- [x] Comando `copamind llm benchmark` (uso ao vivo)

**Aceite:** três boxes; um modelo por vez; fallback; claims ligados a evidências; benchmark. ✅ (chat na UI = E8b)

---

## E8 — Interface bilíngue (Dashboard + Chat)
Objetivo: UI EN/PT-BR polida. E8a (dashboard MVP) precede E8b (UI completa).

### E8a — Dashboard MVP ✅
#### H8.2 — Dashboard
- [x] Ranking de título + gráfico de barras
- [x] Análise de seleção (Elo + forma + últimas partidas)
- [x] Previsão de partida (1x2, gols esperados, placar provável)
- [x] i18n EN/PT-BR na UI
- [ ] Árvore de mata-mata (bracket) visual — futuro (requer bracket real >4 times)
- [x] Curva de calibração (E8b)
- [x] Aba Bolão (E11)

### E8b — UI completa ✅ (core)
#### H8.1 — i18n
- [x] PT-BR default + EN; chaves por seção; seleção de idioma
- [x] Dados canônicos não traduzidos
#### H8.3 — Chat
- [x] Página de chat com 3 boxes (analista/challenger/auditor) + consenso
- [x] Curva de calibração (reliability) no dashboard
- [x] Resposta no idioma da sessão (`response_language`)
- [x] Eventos SSE (`POST /chat/stream` + `run_events`)
#### H8.4 — Camadas
- [x] Streamlit (MVP); Reflex — evolução

**Aceite:** troca de idioma sem hardcode; respostas no idioma escolhido; 3 boxes + consenso; calibração visível. ✅

### E8b — UI completa
#### H8.1 — i18n
- [ ] PT-BR default + EN; chaves de tradução por namespace; seletor; detecção `Accept-Language`
- [ ] Formatação de números/datas por locale; disclaimer bilíngue
- [ ] Dados canônicos não traduzidos (`snapshot_id`, `evidence_ids`, códigos FIFA)
#### H8.3 — Chat
- [ ] Eventos SSE (interpretando → consultando → prevendo → analista → challenger → auditor → consenso)
- [ ] Boxes por modelo + consenso; fontes e lineage
- [ ] Resposta no idioma da sessão (`response_language`)
#### H8.4 — Camadas
- [ ] Streamlit (MVP) e Reflex (demo pública)

**Aceite:** troca de idioma sem hardcode; respostas no idioma escolhido; demo local documentada + screenshots.

---

## E9 — Conteúdo & Publicação ✅ (core)
Objetivo: publicar no GitHub e gerar conteúdo para LinkedIn.

### H9.1 — GitHub
- [x] README com badges, recursos e instalação; CONTRIBUTING, SECURITY, MODEL_CARD, LICENSE
- [x] Templates de issue (bug/feature/data source) e PR
### H9.2 — Geração de conteúdo
- [x] Cards de ranking e confronto em PT-BR **e** EN (`copamind content ...`)
### H9.3 — Backtest ao vivo
- [x] Bolão registra previsão vs resultado com Brier (E11); cards prontos p/ divulgação

**Aceite:** repositório público completo; disclaimer presente; conteúdo bilíngue gerado. ✅ (falta apenas `git push` e imagens/gifs)

---

## E10 — Evolução: servidor 24 GB VRAM (pós-férias)
Objetivo: escalar sem reescrever, via perfis de hardware. Não bloqueia o MVP em 8 GB.

### H10.1 — Perfis de hardware
- [ ] `hardware_profile: 8gb | 24gb` em `models.yaml`; seleção de roster/quant/contexto
- [ ] `copamind doctor` detecta VRAM e sugere perfil
### H10.2 — Roster 24 GB
- [ ] Validar Gemma 3 27B, Qwen3-32B/30B-A3B, DeepSeek-R1-Distill-32B, Mixtral 8x7B; medir tokens/s e VRAM
### H10.3 — Execução concorrente (opt-in)
- [ ] Carregar 2 modelos simultâneos; **sequencial permanece o default reprodutível**
### H10.4 — QLoRA do auditor
- [ ] Fine-tune leve do auditor para grounding/validação de claims
### H10.5 — GPU para reranker/embeddings + MC paralelo
- [ ] Reranker/embeddings maiores na GPU; simulação Monte Carlo acelerada
### H10.6 — Benchmark 8GB vs 24GB
- [ ] Rodar o harness da E7 nos dois perfis → conteúdo comparativo

**Aceite:** trocar de perfil sem alterar código de aplicação; sequencial continua default e reprodutível; leaderboard 8GB vs 24GB.

---

## E11 — Bolão de IAs Locais (Live Prediction Pool) — feature headline ✅
Objetivo: competição pública entre preditores ao longo da Copa.

### H11.1 — Palpites travados
- [x] Cada preditor (Poisson + Elo; LLMs no E7) gera palpite pré-jogo
- [x] Persistir com `snapshot_id` + `locked_at` (imutável); tabela `pool_predictions`
### H11.2 — Ingestão de resultado
- [x] Resultado real registrado; tabela `pool_results`
### H11.3 — Scoring & leaderboard
- [x] Motor de pontuação (bolão: exato/resultado) + Brier; classificação por preditor
### H11.4 — Dashboard do bolão
- [x] Aba Bolão (leaderboard) no dashboard
### H11.5 — Geração de card
- [ ] Card por rodada em PT-BR e EN — E9

**Aceite:** palpites imutáveis após travados; resultado só entra depois; leaderboard reproduzível; anti-leakage (as_of por partida). ✅
