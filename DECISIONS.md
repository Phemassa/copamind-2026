# DECISIONS.md — Registro de Decisões Arquiteturais (ADR)

> Formato leve. Cada decisão: contexto, decisão, consequências. Ordem cronológica.

---

## ADR-0001 — LLM não produz probabilidades
- **Contexto:** LLMs alucinam e não são calibrados para previsão numérica.
- **Decisão:** as probabilidades vêm exclusivamente de ML/estatística (Elo, Poisson/Dixon-Coles, CatBoost, XGBoost, ensemble calibrado, Monte Carlo). O LLM apenas interpreta, consulta ferramentas e explica. O LLM **nunca** sobrescreve a probabilidade do ML.
- **Consequências:** resultados reproduzíveis e auditáveis; o LLM vira camada de explicação.

## ADR-0002 — Execução sequencial de LLMs como default reprodutível
- **Contexto:** 8 GB de VRAM comportam 1 modelo por vez.
- **Decisão:** pipeline analista → challenger → auditor → consenso, com load/unload sequencial. Concorrência é **opt-in** apenas no perfil de hardware 24 GB; o default permanece sequencial.
- **Consequências:** reprodutibilidade independente do hardware; latência maior no MVP, aceitável.

## ADR-0003 — Suporte multi-hardware via perfis de configuração
- **Contexto:** hoje 8 GB (RTX 5070 Laptop); em breve servidor 24 GB.
- **Decisão:** `hardware_profile: 8gb | 24gb` em `models.yaml` controla roster, quantização, contexto e concorrência. Sem refatoração de código de aplicação.
- **Consequências:** escala por configuração; abstração de backend de LLM isola o hardware.

## ADR-0004 — Roster de modelos locais (máx. 1–2 por marca)
- **Contexto:** benchmark comparativo entre famílias.
- **Decisão:** Qwen3-8B/4B (Alibaba), Gemma 3 12B / Gemma 4 (Google), Llama 3.1 8B (Meta), Ministral 8B/Nemo 12B (Mistral), Phi-4 (Microsoft), DeepSeek-R1-Distill-Qwen-7B (DeepSeek). Nomes ficam em `models.yaml`, nunca no código.
- **Consequências:** diversidade de opinião real; troca de modelos sem tocar no código. *Pendência:* confirmar specs de Gemma 4 / Qwen3 / Phi-4.

## ADR-0005 — RAG multilíngue com bge-m3 + reranker
- **Contexto:** conteúdo majoritariamente em português; qualidade de recuperação é crítica.
- **Decisão:** embeddings **bge-m3** (denso+esparso) + BM25 + **bge-reranker-v2-m3**, em Qdrant.
- **Consequências:** boa recuperação PT/EN; um passo extra de reranking.

## ADR-0006 — Interface bilíngue EN / PT-BR
- **Contexto:** projeto de portfólio para alcance internacional e nacional.
- **Decisão:** PT-BR default, EN segundo idioma. Apenas apresentação é traduzida; dados factuais e lineage (`snapshot_id`, `evidence_ids`, códigos FIFA) permanecem canônicos. Respostas dos LLMs seguem `response_language` da sessão.
- **Consequências:** dobra o alcance; exige disciplina de chaves de tradução e testes.

## ADR-0007 — Stack de UI: Streamlit + Reflex (Python)
- **Contexto:** velocidade no MVP + polimento na demo pública, mantendo Python.
- **Decisão:** Streamlit para MVP interno/backtest; Reflex para a demo pública.
- **Consequências:** sem sair do ecossistema Python; React fica como evolução opcional.

## ADR-0008 — Orquestração com Pydantic AI (ou LangGraph)
- **Contexto:** stack já usa Pydantic v2; máquina de estados do agente definida.
- **Decisão:** Pydantic AI como primeira opção; LangGraph se precisar de máquina de estados explícita.
- **Consequências:** saída estruturada nativa; menos código de cola.

## ADR-0009 — Benchmark de LLMs como feature de primeira classe
- **Contexto:** objetivo de portfólio + comparação entre modelos.
- **Decisão:** harness pontua groundedness, aderência a schema, concordância com ML, latência, tokens/s, VRAM e load/unload; expõe leaderboard local.
- **Consequências:** gera conteúdo; adiciona custo de instrumentação.

## ADR-0010 — Bolão de IAs Locais com palpites imutáveis
- **Contexto:** engajamento durante a Copa + prova de calibração.
- **Decisão:** cada preditor crava palpite antes do apito, travado com `snapshot_id` + `locked_at` (imutável). Resultado real só entra após o jogo; snapshot incremental alimenta a próxima rodada.
- **Consequências:** sem leakage; reprodutível; base para cards recorrentes. Novas tabelas: `pool_predictions`, `pool_results`, `pool_leaderboard`.

## ADR-0011 — Reordenação para slice vertical (timing da Copa)
- **Contexto:** Copa 2026 em andamento (final 19/07/2026).
- **Decisão:** priorizar dados → Elo/Poisson → simulação → dashboard/bracket/cards → bolão, antes de RAG/MCP/orquestração completa de LLMs.
- **Consequências:** valor visível e engajamento cedo; RAG/MCP/LLM entram depois.

## ADR-0012 — Fontes de dados abertas e redistribuíveis
- **Contexto:** repositório público exige dados com licença clara.
- **Decisão:** base estática offline como bootstrap (**OpenFootball `worldcup.json`** — calendário/chaveamento das 104 partidas da Copa 2026; StatsBomb Open Data para histórico com xG). APIs de plano gratuito **apenas para atualização ao vivo, sempre com cache local**: football-data.org (~10/min), API-Football (~100/dia), Zafronix (~250/dia, histórico 1930–2026). Chaves de API somente no `.env`. Sem scraping proibido por ToS.
- **Consequências:** dataset legível offline e redistribuível; consumo de API minimizado por cache; cobertura complementada por user reports (E2) e pelo Bolão (E11).

## ADR-0013 — Machine learning ampliado
- **Contexto:** melhorar qualidade e explicabilidade.
- **Decisão:** adicionar SHAP, validação walk-forward, Optuna (Brier/Log-Loss), incerteza (bootstrap/MC), **stacking com pesos aprendidos** (substitui pesos fixos do ensemble) e detecção de drift.
- **Consequências:** modelos mais robustos e explicáveis; mais complexidade de avaliação.
