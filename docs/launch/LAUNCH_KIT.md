# Kit de Lançamento — CopaMind 2026

Materiais prontos para publicar o projeto. Repositório: https://github.com/Phemassa/copamind-2026

---

## 1. GitHub topics (colar em Settings → Topics)

```
local-llm rag mcp ai-agents machine-learning football-analytics world-cup
monte-carlo lm-studio fastapi duckdb qdrant python open-source sports-analytics
```

## 2. Social preview

- Suba o banner em `docs/assets/copamind-hero.png` (1280×640).
- Settings → General → Social preview → enviar a mesma imagem.

## 3. GitHub Pages

- Settings → Pages → Source: **Deploy from a branch** → `main` / `/docs`.
- URL: https://phemassa.github.io/copamind-2026/

---

## 4. Release v0.1.0 — Public Beta

**Título:** `v0.1.0 — Public Beta`

**Descrição:**

> Primeira versão pública do CopaMind 2026 — plataforma local e open source de
> inteligência esportiva. As probabilidades vêm de modelos de ML calibrados;
> os LLMs locais interpretam e explicam.
>
> **Destaques**
> - Modelos: Elo, Poisson/Dixon-Coles, ensemble, calibração (Brier/LogLoss/ECE)
> - Simulação Monte Carlo do torneio (reprodutível por seed)
> - Bolão de IAs (palpites imutáveis, leaderboard, anti-leakage)
> - RAG híbrido (Qdrant/bge-m3) com proteção anti prompt-injection
> - Orquestração de LLMs locais (analista → challenger → auditor → consenso) + benchmark
> - MCP (`copamind-mcp`), dashboard bilíngue (EN/PT-BR) + chat SSE
> - Ingestão real via OpenFootball `worldcup.json`
> - Perfis de hardware 8 GB / 24 GB
>
> **Como começar**
> ```bash
> pip install -e ".[data,dev]"
> copamind ingest sample && copamind simulate
> pip install -e ".[ui]" && copamind ui serve
> ```
>
> **Limitações conhecidas:** dataset de exemplo é sintético; CatBoost/XGBoost/SHAP
> aguardam histórico real multi-Copa; chat exige LM Studio com modelos configurados.
>
> Projeto independente. Probabilidades experimentais e educacionais.

---

## 5. Roteiro do vídeo (45–75s)

1. Abertura (texto/voz): "Perguntei a três modelos locais quem deve ganhar a Copa. Mas eles não decidem sozinhos."
2. Chat: a pergunta sendo enviada.
3. Agente consultando dados (RAG/MCP) — eventos em sequência.
4. Box estatístico (probabilidades do ensemble/Monte Carlo).
5. Box do analista (ex.: Qwen3-8B).
6. Box do challenger (ex.: Llama/Gemma).
7. Box do auditor validando os claims.
8. Consenso final + ranking de chances de título.
9. Card final com o link do GitHub.

Dica: não comece explicando tecnologia; comece pela pergunta.

---

## 6. Carrossel LinkedIn (8 páginas)

1. Construí uma IA local para analisar a Copa.
2. Por que um LLM sozinho não deveria prever futebol.
3. Base de dados: seleções, jogadores, técnicos, táticas, últimas partidas.
4. Elo, Poisson, CatBoost e ensemble calibrado.
5. Simulação Monte Carlo (milhares de torneios).
6. RAG, MCP e um mini agente.
7. Três LLMs locais em sequência + auditor + consenso.
8. Open source: baixe, rode e contribua → link do GitHub.

---

## 7. Post principal (LinkedIn)

⚽ Construí uma plataforma de IA **local** para analisar e simular a Copa de 2026.

Mas não queria apenas perguntar a um LLM: "quem será campeão?"

LLMs são ótimos para interpretar contexto e explicar cenários — mas não deveriam inventar probabilidades.

Por isso o **CopaMind 2026** combina:

▪️ Dados históricos, jogadores, técnicos, táticas e confrontos
▪️ Forma das últimas 5, 10 e 15 partidas
▪️ Elo, Poisson, ensemble preditivo e calibração
▪️ Milhares de simulações Monte Carlo
▪️ RAG para análises e informações do usuário
▪️ MCP e um mini agente para consultar dados e ferramentas
▪️ LLMs locais respondendo em sequência
▪️ Um auditor que verifica as afirmações e produz um consenso

Tudo local: LM Studio, Python, DuckDB, Qdrant e modelos quantizados.

A Copa é o caso de uso. Na prática, é um laboratório open source de IA aplicada, agentes, dados e explicabilidade.

Código, arquitetura e instalação no GitHub:
https://github.com/Phemassa/copamind-2026

Contribuições, testes em outros equipamentos e novas fontes de dados são bem-vindos.

\#LocalAI #MachineLearning #RAG #MCP #AIAgents #OpenSource #SportsAnalytics

---

## 8. Chamadas de contribuição (Issues)

Labels: `good first issue`, `help wanted`, `data-source`, `model-evaluation`, `documentation`, `frontend`.

Peça ações específicas: rodar no próprio PC e reportar hardware/desempenho; sugerir fonte de dados;
criar conector para outra API; enviar análise tática para a RAG; comparar com o modelo favorito.
