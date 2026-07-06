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
- [ ] Modelo adicional para diversidade de ensemble
#### H3.6 — Ensemble & calibração
- [ ] Stacking com **pesos aprendidos** em validação temporal
- [ ] Platt scaling, isotônica, curva de calibração, Brier, Log-Loss, ECE
#### H3.7 — Explicabilidade & incerteza
- [ ] SHAP / feature importance
- [ ] Intervalos de incerteza (bootstrap / distribuição Monte Carlo)
#### H3.8 — Anti-vazamento temporal
- [ ] Validação walk-forward; `cutoff_timestamp` por dataset; testes de leakage

**Aceite:** rating reproduzível; probabilidades somam ~1; backtest e métricas documentados; artefatos versionados; sem leakage.

---

## E4 — Simulação Monte Carlo
Objetivo: simulador do torneio independente dos LLMs.

### H4.1 — Regras do torneio
- [ ] Grupos, melhores terceiros, mata-mata, prorrogação, pênaltis, chaveamento, desempate
### H4.2 — Motor Monte Carlo
- [ ] Vetorização NumPy, seed reproduzível, 10k/100k simulações
### H4.3 — Saídas & persistência
- [ ] Probabilidade por fase/título, adversários prováveis, caminhos difíceis; persistência + API

**Aceite:** 10.000 simulações em segundos; resultados somam corretamente; testes de chaveamento; seed reproduzível.

---

## E2 — User Reports & Memória
Objetivo: ingestão de texto livre do usuário com ciclo de vida controlado.

### H2.1 — Ingestão de texto livre
- [ ] Endpoint POST + classificação de tipo
- [ ] Extração estruturada por LLM pequeno (Qwen3-4B) + validação de schema
- [ ] Detecção de entidades e ambiguidade
### H2.2 — Ciclo de vida
- [ ] Listar / editar / excluir / verificar / promover
- [ ] Versionamento (sem apagar histórico)
- [ ] Marcação `source_type=user_input`, `verified=false`, `confidence`

**Aceite:** salvar/recuperar por seleção; corrigir; impedir promoção automática ao treino; impedir uso no RAG quando solicitado.

---

## E5 — RAG
Objetivo: recuperação híbrida segura, multilíngue e auditável.

### H5.1 — Indexação
- [ ] Chunking + metadados completos (§12.3)
- [ ] Embeddings **bge-m3** em Qdrant
### H5.2 — Busca híbrida
- [ ] Denso + BM25 + filtros (seleção/jogador/data/fonte)
- [ ] Reranking **bge-reranker-v2-m3** + pesos de recência/confiabilidade
### H5.3 — Segurança
- [ ] Tratar contexto como não confiável; proteção anti prompt-injection
- [ ] Citations e registro de documentos que influenciaram a resposta
### H5.4 — Avaliação
- [ ] Dataset de eval: recall@k, precision@k, MRR, groundedness, citation accuracy

**Aceite:** busca híbrida retorna documentos esperados; injeção bloqueada; citações registradas.

---

## E6 — MCP (`copamind-mcp`)
Objetivo: expor ferramentas locais ao agente com menor privilégio.

### H6.1 — Tools read-only
- [ ] Dados (`get_last_matches`, `get_team_form`, `get_head_to_head`, …)
- [ ] Predição (`predict_match`, `run_tournament_simulation`, `get_champion_probabilities`, …)
- [ ] RAG (`search_knowledge`, `get_retrieved_context`, …)
- [ ] Auditoria (`get_snapshot`, `get_prediction_lineage`, `validate_answer_claims`, …)
### H6.2 — Tools de escrita
- [ ] User reports (`add/update/delete/verify`), separadas, com confirmação
### H6.3 — Segurança
- [ ] Menor privilégio, filesystem restrito, nunca expor `.env`, args validados por Pydantic, logs, timeouts, limites de payload

**Aceite:** agente consulta jogos/previsão/RAG; logs mostram lineage; read-only e write separadas.

---

## E7 — Orquestração de LLMs + Benchmark
Objetivo: execução sequencial com unload, consenso auditável e benchmark local.

### H7.1 — Cliente & perfis
- [ ] Cliente LM Studio (OpenAI-compat) + Ollama
- [ ] `models.yaml` (papel, contexto, temperatura, unload, retry, fallback, `hardware_profile`)
- [ ] Saída estruturada por JSON Schema (inclui `response_language`)
### H7.2 — Pipeline sequencial
- [ ] analista → unload → challenger → unload → auditor → unload → consenso
- [ ] Máquina de estados (Pydantic AI / LangGraph)
- [ ] Falha de um modelo não derruba a sessão; fallback disponível
### H7.3 — Grounding & auditoria
- [ ] Claims ligados a `evidence_id`
- [ ] Auditor marca suportado/parcial/não suportado/contraditório/desatualizado
### H7.4 — Benchmark harness (feature)
- [ ] Métricas: groundedness, aderência a schema, concordância com ML, latência, tokens/s, VRAM, load/unload
- [ ] **Leaderboard local** + export para conteúdo

**Aceite:** três boxes; um modelo por vez; fallback; claims ligados a evidências; leaderboard gerado.

---

## E8 — Interface bilíngue (Dashboard + Chat)
Objetivo: UI EN/PT-BR polida. E8a (dashboard MVP) precede E8b (UI completa).

### E8a — Dashboard MVP
#### H8.2 — Dashboard
- [ ] Ranking de título + incerteza
- [ ] **Árvore de mata-mata (bracket)**
- [ ] Evolução da probabilidade ao longo do tempo
- [ ] Radar head-to-head
- [ ] Curva de calibração (reliability diagram)
- [ ] **Aba Bolão** (leaderboard das IAs)

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

## E9 — Conteúdo & Publicação
Objetivo: publicar no GitHub e gerar conteúdo para LinkedIn.

### H9.1 — GitHub
- [ ] README bilíngue, arquitetura, ROADMAP, CONTRIBUTING, SECURITY, LICENSE, MODEL_CARD
- [ ] Templates de issue/PR; release; disclaimer público
### H9.2 — Geração de conteúdo
- [ ] Cards de confronto, gráfico de chances, comparação entre LLMs — em PT-BR **e** EN
### H9.3 — Backtest ao vivo
- [ ] Publicar previsão antes do jogo e mostrar acerto + Brier depois

**Aceite:** repositório público completo; disclaimer presente; conteúdo bilíngue gerado.

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

## E11 — Bolão de IAs Locais (Live Prediction Pool) — feature headline
Objetivo: competição pública entre preditores ao longo da Copa.

### H11.1 — Palpites travados
- [ ] Cada preditor (ensemble ML + cada LLM) gera palpite pré-jogo
- [ ] Persistir com `snapshot_id` + `locked_at` (imutável); tabela `pool_predictions`
### H11.2 — Ingestão de resultado
- [ ] Resultado real pós-jogo (user report / API aberta); atualização incremental do snapshot; tabela `pool_results`
### H11.3 — Scoring & leaderboard
- [ ] Motor de pontuação (bolão: 1x2, placar exato, diff gols) + qualidade (Brier/Log-Loss)
- [ ] Acumulado por rodada/torneio; tabela `pool_leaderboard`
### H11.4 — Dashboard do bolão
- [ ] Placar acumulado, evolução por rodada, "IA da rodada", casa (ML) vs LLMs
### H11.5 — Geração de card
- [ ] Card por jogo/rodada em PT-BR e EN para LinkedIn

**Aceite:** palpites imutáveis após kickoff; resultado só entra depois; leaderboard reproduzível por snapshot; card bilíngue gerado.
