# ROADMAP.md — CopaMind 2026

> Ordenado por valor de engajamento (a Copa 2026 termina em 19/07/2026). Referência de escopo: `MASTER_PLAN` §37; backlog detalhado: `TASKS.md`.

## Marco 1 — MVP público jogável (prioridade máxima)
Entregar o mais rápido possível um caminho fim-a-fim que já gera conteúdo.

- **E0** Fundação & DevEx
- **E1** Dados & Ingestão (dataset redistribuível)
- **E3a** Elo + forma recente
- **E4** Poisson / Dixon-Coles
- **E4b** Simulação Monte Carlo
- **E8a** Dashboard + bracket + curva de calibração
- **E11** Bolão de IAs Locais (palpites + resultado + leaderboard)

**Resultado:** probabilidades por confronto, chances de título, bracket e bolão ao vivo — pronto para posts.

## Marco 2 — Conhecimento e agentes
- **E2** User reports & memória
- **E5** RAG (bge-m3 + reranker)
- **E6** MCP (`copamind-mcp`)
- **E7** Orquestração de LLMs + benchmark (leaderboard local)

**Resultado:** chat com evidências, três boxes + consenso, benchmark de modelos locais.

## Marco 3 — Robustez preditiva e UI final
- **E3b** CatBoost, XGBoost, ensemble com stacking aprendido, calibração, SHAP, incerteza
- **E8b** UI completa bilíngue (EN/PT-BR), chat SSE, Reflex

**Resultado:** previsões mais fortes, calibradas e explicáveis; interface polida internacional.

## Marco 4 — Publicação
- **E9** GitHub (README bilíngue, docs, templates, release) + geração de conteúdo PT/EN + backtest ao vivo

**Resultado:** repositório público + narrativa de lançamento no LinkedIn.

## Marco 5 — Evolução 24 GB (pós-férias)
- **E10** Perfis de hardware, roster 27–32B, execução concorrente opt-in, QLoRA do auditor, benchmark 8GB vs 24GB

**Resultado:** escala sem reescrita; comparativo de hardware como conteúdo.

---

### Fora de escopo (mantido do plano original)
Treino de LLM do zero; fine-tune > 4B (exceto QLoRA do auditor no Marco 5); ingestão de vídeo; apostas/integração com casas de apostas; execução simultânea de LLMs no MVP; scraping proibido por ToS; Kubernetes; app móvel nativo.
