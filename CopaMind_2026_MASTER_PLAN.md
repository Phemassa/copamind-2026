# CopaMind 2026 — Plano Mestre de Desenvolvimento

> **Nome de trabalho:** CopaMind 2026  
> **Tipo:** projeto open source para GitHub  
> **Objetivo:** coletar dados de seleções, jogadores, técnicos, táticas e partidas; treinar modelos preditivos locais; simular a Copa de 2026; disponibilizar um chat com RAG, MCP e respostas sequenciais de múltiplos modelos locais.  
> **Ambiente-alvo inicial:** Windows 11, Python, Docker Desktop, VS Code, LM Studio e GPU NVIDIA RTX 5070 Laptop com 8 GB de VRAM.  
> **Data-base do planejamento:** 6 de julho de 2026.  
> **Aviso:** este projeto não possui vínculo oficial com FIFA, seleções, federações ou organizadores do torneio.

---

# 1. Instruções principais para o Opus

Você atuará como arquiteto de software, engenheiro de dados, engenheiro de machine learning e desenvolvedor full stack deste projeto.

## Regras de execução

1. Não tente implementar todo o projeto em uma única alteração.
2. Trabalhe por fases e pequenos incrementos verificáveis.
3. Antes de iniciar uma fase:
   - leia este arquivo;
   - leia `TASKS.md`;
   - leia `DECISIONS.md`;
   - leia `CHANGELOG.md`;
   - identifique dependências e riscos.
4. Antes de alterar código existente:
   - inspecione a estrutura do repositório;
   - localize testes relacionados;
   - preserve compatibilidade;
   - documente decisões relevantes.
5. Cada entrega deve conter:
   - código;
   - testes;
   - documentação;
   - comandos de execução;
   - critérios de aceite verificados.
6. Não invente dados reais de partidas, jogadores, lesões ou escalações.
7. Todo dado deve possuir:
   - origem;
   - data de coleta;
   - data de validade;
   - nível de confiança;
   - identificador de snapshot.
8. Nunca permitir vazamento temporal no treinamento.
9. Nunca inserir automaticamente dados fornecidos pelo usuário no conjunto oficial de treino sem validação.
10. Sempre preferir componentes locais e open source.
11. Chaves de API nunca devem ser incluídas no Git.
12. Mantenha o projeto executável em máquina local com 32 GB de RAM e 8 GB de VRAM.
13. Modelos LLM devem ser executados de forma sequencial, não simultânea.
14. Atualize `TASKS.md` ao concluir cada item.
15. Registre decisões arquiteturais em `DECISIONS.md`.
16. Quando uma alteração quebrar compatibilidade, documente a migração.
17. Use tipagem, lint, testes automatizados e tratamento de erros desde o início.
18. Não use scraping proibido pelos termos de uso das fontes.
19. Não utilizar marcas, logos ou identidades visuais oficiais sem permissão.
20. A previsão deve ser apresentada como probabilidade, nunca como certeza.

---

# 2. Visão do produto

O CopaMind 2026 será uma plataforma local e open source de inteligência esportiva capaz de:

- importar dados históricos de futebol;
- registrar as últimas partidas das seleções;
- armazenar dados informados manualmente pelo usuário;
- calcular métricas de forma recente;
- estimar força ofensiva e defensiva;
- analisar técnicos, jogadores, escalações e táticas;
- treinar modelos estatísticos e de machine learning;
- prever vitória, empate, derrota e placares;
- simular o torneio milhares de vezes;
- estimar chances de classificação e título;
- responder perguntas por chat;
- usar RAG para recuperar dados estruturados e textuais;
- usar MCP para expor ferramentas e fontes ao agente;
- executar vários LLMs locais em sequência;
- exibir uma resposta independente de cada modelo;
- gerar uma síntese final auditável;
- registrar o snapshot de dados utilizado em cada resposta.

---

# 3. Objetivos do MVP

O MVP deve permitir que uma pessoa:

1. instale o projeto localmente;
2. carregue uma base histórica inicial;
3. cadastre ou importe seleções e partidas;
4. informe manualmente partidas recentes;
5. gere features pré-jogo;
6. treine pelo menos:
   - Elo;
   - Poisson;
   - CatBoost;
7. simule a Copa;
8. visualize probabilidades;
9. faça uma pergunta no chat;
10. acompanhe três respostas sequenciais:
    - modelo principal;
    - segunda opinião;
    - auditor;
11. veja uma resposta final de consenso;
12. verifique quais dados, documentos e previsões foram utilizados.

---

# 4. Fora do escopo inicial

Não implementar no MVP:

- treinamento de LLM do zero;
- fine-tuning de modelos maiores que 4B;
- ingestão automática de vídeo;
- reconhecimento visual de partidas;
- apostas automáticas;
- integração com casas de apostas;
- execução simultânea de vários LLMs;
- previsão baseada apenas em opinião de LLM;
- scraping de sites que proíbam automação;
- armazenamento de material protegido sem autorização;
- aplicativo móvel nativo;
- infraestrutura Kubernetes;
- autenticação corporativa complexa;
- arquitetura distribuída em múltiplos nós.

---

# 5. Princípios técnicos

## 5.1 A previsão não será produzida diretamente pelo LLM

O LLM deve interpretar, consultar e explicar.

As probabilidades serão produzidas por:

- Elo;
- Poisson ou Dixon-Coles;
- regressão logística;
- CatBoost;
- XGBoost ou LightGBM;
- modelo bayesiano opcional;
- ensemble calibrado;
- simulação Monte Carlo.

## 5.2 Dados estruturados e dados textuais são camadas diferentes

### Dados estruturados

Exemplos:

- partidas;
- placares;
- escalações;
- jogadores;
- minutos;
- cartões;
- formações;
- métricas;
- rankings;
- previsões.

Armazenamento inicial:

- DuckDB;
- Parquet;
- Polars.

### Dados textuais

Exemplos:

- análise tática;
- notícia de lesão;
- relato do usuário;
- observação sobre técnico;
- resumo de confronto;
- scout textual;
- respostas anteriores.

Armazenamento inicial:

- documentos em arquivos;
- metadados em DuckDB;
- embeddings em Qdrant.

## 5.3 Todo resultado deve ser reproduzível

Cada previsão deve registrar:

- `snapshot_id`;
- versão do dataset;
- versão das features;
- versão do modelo;
- parâmetros;
- seed;
- data e hora;
- origem dos dados;
- modelos LLM utilizados;
- prompts;
- documentos recuperados;
- tempos de execução.

---

# 6. Arquitetura de alto nível

```text
┌──────────────────────────────────────────────────────────────┐
│                         FONTES DE DADOS                       │
│ APIs | arquivos | CSV | JSON | fontes oficiais | usuário    │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    CAMADA DE INGESTÃO                         │
│ Connectors | importadores | validação | deduplicação         │
└───────────────────────────────┬──────────────────────────────┘
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
┌──────────────────────────┐       ┌────────────────────────────┐
│ DATA LAKE LOCAL          │       │ BASE TEXTUAL               │
│ raw/bronze/silver/gold   │       │ documentos + metadados     │
│ Parquet + DuckDB         │       │ Qdrant                     │
└─────────────┬────────────┘       └──────────────┬─────────────┘
              │                                   │
              ▼                                   ▼
┌──────────────────────────┐       ┌────────────────────────────┐
│ FEATURE ENGINEERING      │       │ RAG                        │
│ forma, força, contexto   │       │ busca híbrida e filtros    │
└─────────────┬────────────┘       └──────────────┬─────────────┘
              │                                   │
              ▼                                   │
┌──────────────────────────┐                      │
│ MODELOS PREDITIVOS       │                      │
│ Elo/Poisson/CatBoost     │                      │
│ ensemble/calibração      │                      │
└─────────────┬────────────┘                      │
              │                                   │
              ▼                                   │
┌──────────────────────────┐                      │
│ SIMULADOR DO TORNEIO     │                      │
│ Monte Carlo              │                      │
└─────────────┬────────────┘                      │
              └────────────────┬──────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP + MINI AGENTE                          │
│ ferramentas de dados, previsão, RAG, simulação e auditoria   │
└───────────────────────────────┬──────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                 ORQUESTRADOR DE LLMs LOCAIS                  │
│ Modelo A → unload → Modelo B → unload → Auditor → consenso  │
└───────────────────────────────┬──────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                       INTERFACE WEB                           │
│ dashboard | chat | boxes por modelo | fontes | probabilidades│
└──────────────────────────────────────────────────────────────┘
```

---

# 7. Stack recomendada

## Backend

- Python 3.12;
- FastAPI;
- Pydantic v2;
- Uvicorn;
- HTTPX;
- SQLModel ou SQLAlchemy apenas quando necessário;
- Typer para CLI;
- structlog para logs.

## Dados

- DuckDB;
- Polars;
- PyArrow;
- Parquet;
- Pandera para validação;
- dbt-duckdb opcional após o MVP.

## Machine learning

- scikit-learn;
- CatBoost;
- XGBoost;
- Optuna;
- MLflow;
- joblib;
- PyMC opcional.

## RAG

- Qdrant local em Docker;
- FastEmbed ou embeddings via LM Studio;
- busca vetorial;
- busca lexical;
- filtros por seleção, jogador, data e fonte;
- reranking opcional.

## LLM local

- LM Studio;
- API local compatível com OpenAI;
- cliente HTTP próprio;
- JSON Schema para saída estruturada;
- carregamento e descarregamento sequencial.

## Interface

### MVP

- Streamlit.

### Evolução

- React;
- TypeScript;
- Vite;
- TanStack Query;
- componentes acessíveis;
- SSE para acompanhar execução dos modelos.

## Qualidade

- pytest;
- pytest-cov;
- mypy;
- Ruff;
- pre-commit;
- GitHub Actions;
- Bandit;
- pip-audit ou equivalente.

---

# 8. Estrutura do repositório

```text
copamind-2026/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   ├── CONTRIBUTING.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── SECURITY.md
├── apps/
│   ├── api/
│   ├── streamlit/
│   └── web/
├── config/
│   ├── app.example.yaml
│   ├── models.example.yaml
│   ├── sources.example.yaml
│   └── logging.yaml
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   ├── user_input/
│   ├── documents/
│   ├── snapshots/
│   └── README.md
├── docker/
│   ├── qdrant/
│   └── compose.yaml
├── docs/
│   ├── architecture/
│   ├── data/
│   ├── models/
│   ├── rag/
│   ├── mcp/
│   ├── api/
│   └── screenshots/
├── notebooks/
│   ├── exploration/
│   └── validation/
├── scripts/
│   ├── bootstrap.ps1
│   ├── bootstrap.sh
│   ├── download_sample_data.py
│   ├── build_snapshot.py
│   ├── train_models.py
│   └── run_simulation.py
├── src/
│   └── copamind/
│       ├── agents/
│       ├── api/
│       ├── cli/
│       ├── core/
│       ├── data/
│       │   ├── connectors/
│       │   ├── ingestion/
│       │   ├── validation/
│       │   ├── transformations/
│       │   └── repositories/
│       ├── features/
│       ├── llm/
│       ├── mcp/
│       ├── models/
│       │   ├── elo/
│       │   ├── poisson/
│       │   ├── catboost/
│       │   ├── xgboost/
│       │   ├── calibration/
│       │   └── ensemble/
│       ├── rag/
│       ├── simulation/
│       └── observability/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── regression/
│   └── fixtures/
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── DECISIONS.md
├── LICENSE
├── MODEL_CARD.md
├── pyproject.toml
├── README.md
├── ROADMAP.md
├── TASKS.md
└── MASTER_PLAN.md
```

---

# 9. Modelo de dados

## 9.1 Entidades principais

### `teams`

- `team_id`;
- `name`;
- `fifa_code`;
- `country`;
- `confederation`;
- `fifa_ranking`;
- `elo_rating`;
- `active`;
- `valid_from`;
- `valid_to`;
- `source`;
- `collected_at`.

### `coaches`

- `coach_id`;
- `name`;
- `nationality`;
- `team_id`;
- `started_at`;
- `ended_at`;
- `preferred_formations`;
- `matches`;
- `wins`;
- `draws`;
- `losses`;
- `source`;
- `collected_at`.

### `players`

- `player_id`;
- `name`;
- `birth_date`;
- `national_team_id`;
- `club`;
- `position`;
- `preferred_foot`;
- `height_cm`;
- `active`;
- `source`;
- `collected_at`.

### `matches`

- `match_id`;
- `competition`;
- `season`;
- `stage`;
- `match_date`;
- `home_team_id`;
- `away_team_id`;
- `venue_id`;
- `neutral_venue`;
- `home_score`;
- `away_score`;
- `home_score_extra_time`;
- `away_score_extra_time`;
- `home_penalties`;
- `away_penalties`;
- `status`;
- `importance_weight`;
- `source`;
- `collected_at`;
- `available_at`;
- `snapshot_id`.

### `lineups`

- `match_id`;
- `team_id`;
- `player_id`;
- `starter`;
- `shirt_number`;
- `position`;
- `formation_slot`;
- `minutes_played`;
- `captain`;
- `source`.

### `player_match_stats`

- `match_id`;
- `player_id`;
- `minutes`;
- `goals`;
- `assists`;
- `shots`;
- `shots_on_target`;
- `xg`;
- `xa`;
- `passes`;
- `passes_completed`;
- `key_passes`;
- `tackles`;
- `interceptions`;
- `clearances`;
- `saves`;
- `cards`.

### `team_match_stats`

- `match_id`;
- `team_id`;
- `possession`;
- `shots`;
- `shots_on_target`;
- `xg`;
- `passes`;
- `passes_completed`;
- `corners`;
- `fouls`;
- `offsides`;
- `ppda`;
- `field_tilt`;
- `set_piece_xg`;
- `counter_attacks`;
- `high_turnovers`.

### `tactical_profiles`

- `team_id`;
- `valid_from`;
- `valid_to`;
- `base_formation`;
- `alternate_formations`;
- `pressing_style`;
- `defensive_block`;
- `build_up_style`;
- `transition_style`;
- `set_piece_strength`;
- `width`;
- `tempo`;
- `source`;
- `confidence`.

### `availability_events`

- `event_id`;
- `player_id`;
- `team_id`;
- `event_type`;
- `status`;
- `started_at`;
- `expected_end_at`;
- `severity`;
- `impact_score`;
- `source`;
- `verified`;
- `collected_at`.

### `user_reports`

- `report_id`;
- `session_id`;
- `user_text`;
- `parsed_payload`;
- `report_type`;
- `entities`;
- `source_type`;
- `verified`;
- `confidence`;
- `created_at`;
- `available_at`;
- `snapshot_id`.

### `predictions`

- `prediction_id`;
- `snapshot_id`;
- `match_id`;
- `model_name`;
- `model_version`;
- `home_win_probability`;
- `draw_probability`;
- `away_win_probability`;
- `expected_home_goals`;
- `expected_away_goals`;
- `calibration_version`;
- `created_at`.

### `simulation_runs`

- `run_id`;
- `snapshot_id`;
- `model_bundle_version`;
- `iterations`;
- `seed`;
- `started_at`;
- `finished_at`;
- `config_json`.

### `simulation_results`

- `run_id`;
- `team_id`;
- `reach_round_32_probability`;
- `reach_round_16_probability`;
- `reach_quarterfinal_probability`;
- `reach_semifinal_probability`;
- `reach_final_probability`;
- `champion_probability`.

---

# 10. Camadas de dados

## Raw

Cópia fiel da fonte.

Não alterar sem necessidade técnica.

## Bronze

Dados normalizados em estrutura mínima.

- nomes padronizados;
- tipos corrigidos;
- campos obrigatórios;
- identificação de origem.

## Silver

Dados reconciliados e deduplicados.

- entidades vinculadas;
- partidas únicas;
- nomes de equipes resolvidos;
- datas normalizadas;
- validações aplicadas.

## Gold

Dados prontos para analytics e treinamento.

- features por partida;
- forma recente;
- ratings;
- força de jogadores;
- disponibilidade;
- matchup tático;
- contexto;
- datasets temporais.

---

# 11. Ingestão de partidas informadas pelo usuário

A RAG deve aceitar informações como:

> “O Brasil venceu o México por 2 a 1 ontem. Rodrygo e Endrick marcaram. O time jogou no 4-3-3 e teve dificuldades na saída de bola.”

## Fluxo

```text
Entrada do usuário
      │
      ▼
Classificação do tipo de informação
      │
      ▼
Extração estruturada por LLM pequeno
      │
      ▼
Validação de schema
      │
      ▼
Detecção de entidades
      │
      ▼
Detecção de ambiguidade
      │
      ├── baixa ambiguidade → staging
      └── alta ambiguidade → marcado como incompleto
      │
      ▼
Persistência em user_reports
      │
      ▼
Chunk textual + embedding
      │
      ▼
Disponível para RAG
```

## Regras

1. Dados do usuário entram com:
   - `source_type = "user_input"`;
   - `verified = false`;
   - `confidence` calculada;
   - timestamp;
   - texto original preservado.
2. O sistema pode usar esses dados para responder perguntas, mas deve indicar que são informações fornecidas pelo usuário.
3. O sistema não pode inserir esses dados automaticamente no treino oficial.
4. Um processo posterior pode:
   - comparar com outra fonte;
   - marcar como verificado;
   - promover para Silver;
   - incluir em snapshots futuros.
5. O usuário deve conseguir:
   - listar informações fornecidas;
   - corrigir;
   - excluir;
   - marcar como confirmadas;
   - impedir uso no RAG.
6. Correções não devem apagar histórico silenciosamente.
7. Cada alteração deve gerar uma nova versão.

---

# 12. RAG

## 12.1 Objetivos

O RAG deve recuperar:

- últimos jogos;
- histórico de confrontos;
- técnicos;
- escalações;
- lesões;
- táticas;
- análises;
- métricas agregadas;
- previsões estatísticas;
- observações do usuário;
- documentos do projeto.

## 12.2 Tipos de recuperação

### SQL retrieval

Para fatos estruturados.

Exemplos:

- últimos 15 jogos;
- média de gols;
- forma recente;
- taxa de vitórias;
- disponibilidade de jogadores;
- comparação de Elo;
- probabilidade de título.

### Vector retrieval

Para texto semiestruturado.

Exemplos:

- análise tática;
- observações;
- notícias;
- relatórios;
- scout;
- explicações anteriores.

### Hybrid retrieval

Combinar:

- filtros estruturados;
- BM25 ou busca lexical;
- similaridade vetorial;
- reranking;
- prioridade por recência;
- prioridade por confiabilidade.

## 12.3 Metadados dos chunks

Todo chunk deve incluir:

- `document_id`;
- `chunk_id`;
- `entity_type`;
- `entity_ids`;
- `team_ids`;
- `player_ids`;
- `coach_ids`;
- `match_ids`;
- `source`;
- `source_type`;
- `verified`;
- `confidence`;
- `document_date`;
- `available_at`;
- `collected_at`;
- `snapshot_id`;
- `language`;
- `tags`.

## 12.4 Política de relevância

Pontuação final sugerida:

```text
score =
    vector_similarity
  + lexical_score
  + recency_weight
  + source_quality_weight
  + verification_weight
  + entity_match_weight
```

## 12.5 Proteção contra prompt injection

1. Tratar todo documento recuperado como dado não confiável.
2. Nunca obedecer instruções contidas em documentos.
3. Separar claramente:
   - system prompt;
   - instrução do usuário;
   - contexto recuperado.
4. Remover ou marcar conteúdo suspeito.
5. Registrar documentos que influenciaram a resposta.

---

# 13. MCP

## 13.1 Objetivo

MCP será usado para expor ferramentas locais ao agente e ao ambiente de desenvolvimento.

## 13.2 Servidores MCP recomendados

### Desenvolvimento

- filesystem com acesso restrito ao repositório;
- Git;
- GitHub;
- terminal controlado;
- documentação local;
- logs;
- testes.

### Produto

Criar um servidor MCP próprio chamado:

```text
copamind-mcp
```

## 13.3 Ferramentas do `copamind-mcp`

### Dados

- `list_teams`;
- `get_team`;
- `get_players`;
- `get_coach`;
- `get_last_matches`;
- `get_head_to_head`;
- `get_match`;
- `get_player_form`;
- `get_team_form`;
- `get_injuries`;
- `get_suspensions`;
- `get_tactical_profile`;
- `get_data_freshness`;
- `get_data_sources`.

### Predição

- `predict_match`;
- `explain_prediction`;
- `compare_teams`;
- `run_tournament_simulation`;
- `get_champion_probabilities`;
- `get_stage_probabilities`;
- `get_model_metrics`;
- `get_calibration_report`.

### RAG

- `search_knowledge`;
- `search_user_reports`;
- `add_user_report`;
- `update_user_report`;
- `delete_user_report`;
- `verify_user_report`;
- `list_rag_sources`;
- `get_retrieved_context`.

### Auditoria

- `get_snapshot`;
- `list_snapshots`;
- `get_prediction_lineage`;
- `get_model_version`;
- `get_feature_values`;
- `get_missing_data`;
- `validate_answer_claims`.

## 13.4 Segurança do MCP

- aplicar princípio do menor privilégio;
- filesystem restrito;
- bloquear diretórios fora do projeto;
- nunca expor `.env`;
- limitar comandos de terminal;
- validar argumentos com Pydantic;
- logs de todas as chamadas;
- timeouts;
- limites de payload;
- evitar execução arbitrária;
- separar ferramentas read-only e write;
- exigir confirmação da aplicação para ações destrutivas.

---

# 14. Mini agente

## 14.1 Papel

O mini agente será o orquestrador central.

Ele não será responsável por “adivinhar” resultados.

Ele deve:

1. interpretar a pergunta;
2. identificar entidades;
3. escolher ferramentas;
4. buscar dados;
5. chamar modelos preditivos;
6. recuperar contexto textual;
7. montar o pacote de evidências;
8. executar LLMs locais em sequência;
9. auditar respostas;
10. criar consenso;
11. registrar lineage.

## 14.2 Estados do agente

```text
RECEIVED
UNDERSTANDING
PLANNING
RETRIEVING_STRUCTURED_DATA
RETRIEVING_RAG
RUNNING_PREDICTION
RUNNING_MODEL_A
RUNNING_MODEL_B
RUNNING_AUDITOR
BUILDING_CONSENSUS
COMPLETED
FAILED
```

## 14.3 Ferramentas mínimas

- consulta SQL segura;
- busca RAG;
- previsão de partida;
- simulação;
- análise de forma;
- auditoria de claims;
- registro de sessão.

## 14.4 Memória

### Memória de sessão

- perguntas da sessão;
- entidades citadas;
- filtros ativos;
- snapshot;
- respostas anteriores.

### Memória persistente

Somente para:

- relatórios informados pelo usuário;
- preferências de visualização;
- seleções favoritas;
- análises salvas;
- histórico de execuções.

Não armazenar conteúdo desnecessário ou sensível.

## 14.5 Planejamento

O agente deve produzir internamente um plano curto e estruturado:

```json
{
  "intent": "compare_teams",
  "entities": {
    "team_a": "Brazil",
    "team_b": "France"
  },
  "required_tools": [
    "get_team_form",
    "get_head_to_head",
    "get_injuries",
    "predict_match",
    "search_knowledge"
  ],
  "snapshot_policy": "latest_consistent",
  "needs_simulation": false
}
```

---

# 15. LLMs locais

## 15.1 Limites de hardware

Configuração inicial:

- 8 GB de VRAM;
- 32 GB de RAM;
- um modelo carregado por vez;
- contexto inicial entre 8k e 12k;
- quantização Q4;
- streaming;
- unload após uso.

## 15.2 Perfis de modelos

O projeto não deve depender de nomes fixos.

Usar perfis configuráveis.

```yaml
models:
  analyst:
    provider: lmstudio
    model_id: local-model-analyst
    role: primary_analyst
    context_length: 8192
    temperature: 0.2
    unload_after_run: true

  challenger:
    provider: lmstudio
    model_id: local-model-challenger
    role: alternative_analysis
    context_length: 8192
    temperature: 0.25
    unload_after_run: true

  auditor:
    provider: lmstudio
    model_id: local-model-auditor
    role: evidence_auditor
    context_length: 6144
    temperature: 0.0
    unload_after_run: true
```

## 15.3 Execução sequencial

```text
1. montar evidence pack;
2. carregar analyst;
3. gerar resposta estruturada;
4. salvar métricas;
5. descarregar analyst;
6. carregar challenger;
7. gerar resposta independente;
8. salvar métricas;
9. descarregar challenger;
10. carregar auditor;
11. comparar claims;
12. apontar divergências;
13. descarregar auditor;
14. produzir consenso final.
```

## 15.4 Contrato de resposta

```json
{
  "model_role": "primary_analyst",
  "response_language": "pt-BR|en",
  "answer": "texto",
  "predicted_team": "team_id_or_null",
  "confidence": "low|medium|high",
  "supporting_factors": [
    {
      "factor": "forma recente",
      "evidence_ids": ["feature:123", "match:456"]
    }
  ],
  "risk_factors": [],
  "data_gaps": [],
  "claims": [
    {
      "text": "A equipe venceu quatro dos últimos cinco jogos.",
      "evidence_ids": ["match:1", "match:2", "match:3", "match:4", "match:5"]
    }
  ],
  "agrees_with_statistical_model": true
}
```

## 15.5 Regra de grounding

Nenhum claim factual deve ser aceito sem:

- `evidence_id`;
- origem;
- snapshot;
- data.

O auditor deve marcar:

- suportado;
- parcialmente suportado;
- não suportado;
- contraditório;
- desatualizado.

---

# 16. Modelos preditivos

## 16.1 Elo

Implementar primeiro.

Entradas:

- resultado;
- força do adversário;
- mando ou campo neutro;
- importância;
- diferença de gols;
- decaimento temporal.

Saídas:

- rating atual;
- probabilidade esperada;
- histórico do rating.

## 16.2 Poisson ou Dixon-Coles

Objetivo:

- gols esperados;
- matriz de placares;
- probabilidade de vitória;
- empate;
- derrota;
- over/under opcional;
- classificação em mata-mata.

## 16.3 CatBoost

Features:

- Elo;
- ranking;
- forma 5/10/15;
- gols;
- xG;
- xGA;
- qualidade dos adversários;
- técnico;
- formação;
- disponibilidade;
- idade;
- entrosamento;
- descanso;
- viagem;
- mando;
- contexto.

Targets:

- classificação multiclasse;
- gols da casa;
- gols do visitante;
- classificação para próxima fase.

## 16.4 XGBoost

Adicionar após CatBoost para diversidade de ensemble.

## 16.5 Ensemble

Exemplo inicial:

```text
P(final) =
  0.20 * Elo
+ 0.25 * Poisson
+ 0.40 * CatBoost
+ 0.15 * XGBoost
```

Os pesos finais devem ser aprendidos ou selecionados em validação temporal.

## 16.6 Calibração

Implementar:

- Platt scaling;
- isotonic regression;
- calibration curve;
- Brier Score;
- Log Loss;
- Expected Calibration Error.

---

# 17. Feature engineering

## 17.1 Janelas

Para cada seleção:

- últimos 5 jogos;
- últimos 10 jogos;
- últimos 15 jogos;
- últimos 365 dias;
- últimos 730 dias;
- jogos com o técnico atual;
- jogos competitivos;
- jogos amistosos;
- jogos contra adversários do mesmo nível.

## 17.2 Decaimento temporal

```text
weight = exp(-lambda * days_since_match)
```

Tornar `lambda` configurável.

## 17.3 Ajuste por adversário

Métricas devem ser ajustadas por:

- Elo do adversário;
- ranking;
- confederação;
- local;
- importância;
- escalação.

## 17.4 Jogadores

Criar:

- player impact score;
- expected minutes;
- replacement quality;
- squad continuity;
- starter availability;
- goalkeeper form;
- attacking concentration;
- defensive stability.

## 17.5 Técnico

Criar:

- tempo no cargo;
- aproveitamento;
- variação de formação;
- estabilidade;
- desempenho contra formações;
- efeito pós-troca;
- experiência em mata-mata.

## 17.6 Tática

Criar perfis categóricos e numéricos:

- pressão;
- bloco;
- largura;
- intensidade;
- posse;
- transição;
- bolas paradas;
- dependência de cruzamentos;
- vulnerabilidade em transição;
- construção curta;
- jogo direto.

## 17.7 Contexto

- descanso;
- viagem;
- fuso;
- altitude;
- clima;
- estádio;
- torcida;
- necessidade do resultado;
- prorrogação anterior;
- cartões;
- suspensão;
- lesões.

---

# 18. Prevenção de vazamento temporal

Regras obrigatórias:

1. Toda feature deve ser calculada usando apenas dados disponíveis antes da partida.
2. Usar `available_at`, não apenas `match_date`.
3. Escalação confirmada só pode entrar em previsões executadas após sua publicação.
4. Lesão só pode entrar após sua divulgação.
5. Ranking deve usar a versão válida na data.
6. Estatística de clube deve usar snapshot anterior ao jogo.
7. Odds, quando utilizadas, devem ficar em modelo separado.
8. Não utilizar resultado posterior para preencher campo anterior.
9. Validar com testes automatizados de leakage.
10. Cada dataset de treino deve declarar `cutoff_timestamp`.

---

# 19. Simulação da Copa

## 19.1 Motor

Criar simulador independente dos LLMs.

## 19.2 Entradas

- participantes;
- grupos;
- calendário;
- regras;
- chaveamento;
- probabilidades por confronto;
- regras de desempate;
- pênaltis;
- seed.

## 19.3 Saídas

- probabilidade de avançar;
- probabilidade por fase;
- probabilidade de final;
- probabilidade de título;
- adversários mais prováveis;
- caminhos mais difíceis;
- distribuição de resultados.

## 19.4 Performance

Meta inicial:

- 10.000 simulações em segundos;
- 100.000 simulações em tempo aceitável;
- seed reproduzível;
- vetorização com NumPy;
- execução paralela opcional por CPU.

---

# 20. API

## Endpoints mínimos

### Health

```text
GET /health
GET /ready
```

### Dados

```text
GET /teams
GET /teams/{team_id}
GET /teams/{team_id}/form
GET /teams/{team_id}/players
GET /teams/{team_id}/coach
GET /matches
GET /matches/{match_id}
GET /head-to-head
```

### User input

```text
POST /user-reports
GET /user-reports
GET /user-reports/{report_id}
PATCH /user-reports/{report_id}
DELETE /user-reports/{report_id}
POST /user-reports/{report_id}/verify
```

### Predições

```text
POST /predictions/match
GET /predictions/{prediction_id}
POST /simulations
GET /simulations/{run_id}
GET /simulations/{run_id}/champion-probabilities
```

### RAG

```text
POST /rag/search
POST /rag/index
GET /rag/sources
```

### Chat

```text
POST /chat/sessions
POST /chat/sessions/{session_id}/messages
GET /chat/sessions/{session_id}/events
GET /chat/sessions/{session_id}/history
```

---

# 21. Interface do usuário

## 21.1 Página inicial

Mostrar:

- status da base;
- data do último snapshot;
- número de partidas;
- número de jogadores;
- fontes;
- modelos disponíveis;
- última simulação;
- ranking de probabilidades.

## 21.2 Dashboard

- chances de título;
- chances por fase;
- gráfico de evolução;
- comparação de seleções;
- forma recente;
- força ofensiva e defensiva;
- disponibilidade.

## 21.3 Chat

Entrada:

```text
“Compare Brasil e França considerando os últimos 15 jogos,
desfalques, técnico, tática e caminho provável até a final.”
```

Saída em eventos:

```text
[1] Interpretando pergunta
[2] Consultando dados
[3] Executando previsão
[4] Executando modelo analista
[5] Executando segunda opinião
[6] Executando auditor
[7] Criando consenso
```

## 21.4 Boxes

### Box estatístico

- probabilidades;
- gols esperados;
- intervalo;
- versão do modelo;
- snapshot;
- top features.

### Box modelo analista

- resposta;
- confiança;
- fatores;
- riscos;
- fontes.

### Box challenger

- resposta independente;
- divergências;
- cenário alternativo.

### Box auditor

- claims validados;
- claims não suportados;
- dados ausentes;
- qualidade das fontes.

### Box consenso

- resposta final;
- ranking;
- pontos de concordância;
- divergências;
- incertezas;
- data dos dados.

---

# 22. Observabilidade

Registrar:

- duração de ingestão;
- linhas processadas;
- erros por fonte;
- tamanho dos snapshots;
- tempo de feature engineering;
- tempo de treino;
- métricas dos modelos;
- tempo da simulação;
- tempo de carregamento de LLM;
- tokens por segundo;
- VRAM estimada;
- documentos recuperados;
- chamadas MCP;
- falhas de schema;
- claims rejeitados.

Formato:

- logs estruturados JSON;
- correlation ID;
- session ID;
- prediction ID;
- snapshot ID.

---

# 23. Configuração

## `.env.example`

```dotenv
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000

DUCKDB_PATH=./data/copamind.duckdb
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=copamind_knowledge

LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_TIMEOUT_SECONDS=300

MODEL_ANALYST_ID=
MODEL_CHALLENGER_ID=
MODEL_AUDITOR_ID=
EMBEDDING_MODEL_ID=

LOG_LEVEL=INFO
DEFAULT_SNAPSHOT_POLICY=latest_consistent
```

## `models.yaml`

Deve permitir:

- ID;
- papel;
- quantização;
- contexto;
- temperatura;
- timeout;
- schema;
- unload;
- retry;
- fallback.

## `sources.yaml`

Deve permitir:

- fonte;
- tipo;
- URL base;
- autenticação;
- licença;
- taxa;
- campos;
- prioridade;
- confiança;
- habilitada.

---

# 24. CLI

Criar comandos:

```bash
copamind init
copamind ingest sample
copamind ingest file <path>
copamind ingest user-report
copamind validate
copamind build-snapshot
copamind build-features
copamind train elo
copamind train poisson
copamind train catboost
copamind evaluate
copamind simulate
copamind rag index
copamind api serve
copamind ui serve
copamind doctor
```

`copamind doctor` deve verificar:

- Python;
- dependências;
- DuckDB;
- Qdrant;
- LM Studio;
- modelos configurados;
- espaço em disco;
- diretórios;
- arquivos de configuração.

---

# 25. Fases de implementação

> **Reordenação v2 (ver §37):** por causa do timing da Copa 2026 (final em 19/07/2026), a execução prioriza um *slice vertical* de engajamento (dados → Elo/Poisson → simulação → dashboard/bracket/cards) antes de RAG, MCP e orquestração de LLMs. As fases abaixo permanecem como referência de escopo; a ordem operacional e o backlog detalhado (épicos E0–E11) estão em `TASKS.md`. Foram acrescentados dois épicos: **E10 — Evolução 24GB VRAM** e **E11 — Bolão de IAs Locais**.

## Fase 0 — Fundação do repositório

Entregas:

- estrutura;
- `pyproject.toml`;
- lint;
- testes;
- CI;
- documentação;
- licença;
- `.env.example`;
- CLI mínima;
- Docker Compose do Qdrant.

Critérios de aceite:

- `pytest` passa;
- `ruff check .` passa;
- `mypy` passa no pacote principal;
- API responde `/health`;
- Qdrant sobe via Docker;
- README contém instalação inicial.

## Fase 1 — Modelo de dados e ingestão de amostra

Entregas:

- schemas Pydantic;
- tabelas DuckDB;
- ingestão CSV/JSON;
- validação;
- deduplicação;
- dataset de exemplo legalmente redistribuível.

Critérios:

- importar partidas;
- listar seleções;
- consultar últimos jogos;
- rejeitar schema inválido;
- registrar origem e snapshot.

## Fase 2 — User reports e memória RAG

Entregas:

- endpoint de relatório;
- extração estruturada;
- armazenamento;
- versionamento;
- indexação;
- busca;
- exclusão.

Critérios:

- salvar relato;
- recuperar por seleção;
- corrigir relato;
- marcar como não verificado;
- impedir promoção automática para treino.

## Fase 3 — Elo e forma recente

Entregas:

- Elo;
- cálculo de janelas;
- métricas de forma;
- API;
- testes.

Critérios:

- reproduzir rating com seed/config;
- consultar últimos 5/10/15;
- provar ausência de leakage.

## Fase 4 — Poisson

Entregas:

- ataque e defesa;
- matriz de placares;
- probabilidades;
- testes históricos.

Critérios:

- soma das probabilidades próxima de 1;
- previsões persistidas;
- endpoint funcional.

## Fase 5 — CatBoost

Entregas:

- dataset temporal;
- pipeline;
- tuning;
- avaliação;
- model registry.

Critérios:

- backtest;
- métricas registradas;
- artefato versionado;
- feature importance;
- comparação com baseline Elo.

## Fase 6 — Ensemble e calibração

Entregas:

- combinação;
- calibração;
- relatório;
- modelo selecionado.

Critérios:

- não piorar baseline sem justificativa;
- Brier e Log Loss documentados;
- curva de calibração.

## Fase 7 — Simulador

Entregas:

- regras do torneio;
- Monte Carlo;
- probabilidades por fase;
- persistência;
- API.

Critérios:

- seed reproduzível;
- 10.000 simulações;
- resultados somam corretamente;
- testes de chaveamento.

## Fase 8 — MCP

Entregas:

- servidor MCP;
- ferramentas read-only;
- ferramentas de user report;
- auditoria;
- documentação.

Critérios:

- agente consulta últimos jogos;
- agente chama previsão;
- agente recupera RAG;
- logs mostram lineage.

## Fase 9 — LLM orchestration

Entregas:

- cliente LM Studio;
- perfis;
- structured output;
- sequência;
- unload;
- auditor;
- consenso.

Critérios:

- três boxes;
- modelos executados um por vez;
- falha de um modelo não derruba sessão;
- fallback disponível;
- claims vinculados a evidências.

## Fase 10 — Interface pública

Entregas:

- Streamlit;
- dashboard;
- chat;
- SSE ou atualização progressiva;
- fontes;
- lineage;
- exportação.

Critérios:

- instalação documentada;
- demo local;
- screenshots;
- vídeo curto;
- experiência compreensível.

## Fase 11 — Publicação GitHub

Entregas:

- README final;
- arquitetura;
- roadmap;
- contributing;
- issues;
- licença;
- release;
- dados de exemplo;
- modelo de segurança;
- disclaimer.

## Fase 12 — Conteúdo para LinkedIn

Entregas:

- texto de lançamento;
- imagens;
- GIF;
- vídeo;
- instruções;
- link do GitHub;
- roadmap aberto;
- chamada para contribuidores.

---

# 26. Backlog funcional

## Dados

- [ ] importar seleções;
- [ ] importar técnicos;
- [ ] importar jogadores;
- [ ] importar partidas;
- [ ] importar escalações;
- [ ] importar estatísticas;
- [ ] importar disponibilidade;
- [ ] importar táticas;
- [ ] deduplicar entidades;
- [ ] criar snapshots;
- [ ] exibir data freshness.

## User input

- [ ] receber texto livre;
- [ ] classificar conteúdo;
- [ ] extrair entidades;
- [ ] validar;
- [ ] salvar;
- [ ] indexar;
- [ ] editar;
- [ ] excluir;
- [ ] verificar;
- [ ] promover.

## Modelos

- [ ] Elo;
- [ ] Poisson;
- [ ] CatBoost;
- [ ] XGBoost;
- [ ] ensemble;
- [ ] calibração;
- [ ] explicabilidade;
- [ ] backtest.

## Simulação

- [ ] grupos;
- [ ] melhores terceiros;
- [ ] mata-mata;
- [ ] prorrogação;
- [ ] pênaltis;
- [ ] chaveamento;
- [ ] probabilidades;
- [ ] exportação.

## RAG

- [ ] chunks;
- [ ] embeddings;
- [ ] filtros;
- [ ] busca híbrida;
- [ ] reranking;
- [ ] citations;
- [ ] proteção contra injection;
- [ ] evaluation dataset.

## MCP

- [ ] servidor;
- [ ] data tools;
- [ ] prediction tools;
- [ ] RAG tools;
- [ ] simulation tools;
- [ ] audit tools;
- [ ] logs;
- [ ] permissions.

## Chat

- [ ] sessão;
- [ ] streaming;
- [ ] boxes;
- [ ] prompts;
- [ ] structured output;
- [ ] auditor;
- [ ] consenso;
- [ ] lineage;
- [ ] exportação Markdown/JSON.

---

# 27. Estratégia de testes

## Unitários

- schemas;
- cálculo de Elo;
- Poisson;
- features;
- recência;
- normalização;
- regras do torneio;
- parser de user reports.

## Integração

- DuckDB;
- Qdrant;
- LM Studio mockado;
- MCP;
- API;
- pipeline.

## Contrato

- schemas de entrada;
- schemas de saída;
- ferramentas MCP;
- JSON dos LLMs.

## Regressão

- resultados do Elo;
- distribuição Poisson;
- simulação com seed;
- ranking final;
- queries RAG.

## Leakage

Criar testes dedicados que falhem quando:

- feature usa dado futuro;
- snapshot inclui evento posterior;
- disponibilidade não existia na data;
- estatística foi atualizada retroativamente.

## Avaliação de RAG

Criar conjunto com:

- pergunta;
- entidades;
- documentos esperados;
- resposta esperada;
- claims obrigatórios;
- claims proibidos.

Métricas:

- recall@k;
- precision@k;
- MRR;
- groundedness;
- citation accuracy;
- answer completeness.

---

# 28. Segurança, privacidade e licenças

1. Não versionar chaves.
2. Não versionar banco pessoal do usuário.
3. Adicionar `data/user_input/` ao `.gitignore`.
4. Fornecer dados sintéticos ou redistribuíveis.
5. Documentar licenças de cada fonte.
6. Permitir exclusão dos relatos do usuário.
7. Não publicar dados pessoais.
8. Escapar inputs.
9. Validar SQL.
10. Não permitir SQL arbitrário do LLM.
11. Não permitir shell arbitrário pelo agente.
12. Aplicar rate limits.
13. Registrar auditoria.
14. Adicionar disclaimer sobre previsões.
15. Não incentivar apostas.

---

# 29. GitHub

## README deve conter

- apresentação;
- motivação;
- screenshots;
- arquitetura;
- hardware recomendado;
- instalação;
- configuração do LM Studio;
- configuração dos modelos;
- execução;
- ingestão;
- treinamento;
- simulação;
- chat;
- RAG;
- MCP;
- limitações;
- fontes;
- licença;
- contribuição;
- disclaimer.

## Badges sugeridos

- Python;
- CI;
- cobertura;
- licença;
- Ruff;
- mypy;
- status da release.

## Templates

- bug;
- feature;
- data source;
- model evaluation;
- documentation;
- security.

## Branches

- `main`;
- `develop`;
- `feature/*`;
- `fix/*`;
- `docs/*`.

## Commits

Usar Conventional Commits:

```text
feat:
fix:
docs:
test:
refactor:
perf:
build:
ci:
chore:
```

---

# 30. LinkedIn

O projeto deve gerar materiais automaticamente:

- ranking de probabilidades;
- cards de confronto;
- gráfico de chances;
- explicação do ensemble;
- arquitetura;
- vídeo do chat;
- comparação entre LLMs;
- evolução das previsões.

## Narrativa de publicação

1. problema;
2. por que LLM sozinho não é suficiente;
3. arquitetura híbrida;
4. modelos locais;
5. RAG;
6. MCP;
7. simulação;
8. transparência;
9. convite para colaborar;
10. link do GitHub.

## Disclaimer público

> As probabilidades são experimentais e educacionais. Elas dependem da qualidade e atualidade dos dados e não representam garantia de resultado.

---

# 31. Definição de pronto

Uma tarefa só está pronta quando:

- implementação concluída;
- testes passam;
- lint passa;
- tipos passam;
- documentação atualizada;
- erros tratados;
- logs presentes;
- sem segredo exposto;
- critérios de aceite verificados;
- `TASKS.md` atualizado;
- decisão registrada quando aplicável;
- exemplo executável incluído.

---

# 32. Primeira sequência de trabalho para o Opus

Execute na ordem:

## Passo 1

Criar a fundação do repositório:

- `pyproject.toml`;
- pacote `src/copamind`;
- testes;
- Ruff;
- mypy;
- pytest;
- pre-commit;
- GitHub Actions;
- FastAPI com `/health`;
- Typer com `copamind doctor`;
- Docker Compose com Qdrant.

## Passo 2

Criar:

- `README.md`;
- `TASKS.md`;
- `DECISIONS.md`;
- `CHANGELOG.md`;
- `ROADMAP.md`;
- `.env.example`;
- configurações YAML.

## Passo 3

Criar schemas:

- Team;
- Coach;
- Player;
- Match;
- UserReport;
- Snapshot;
- Prediction;
- SimulationRun.

## Passo 4

Criar repositório DuckDB:

- migrations simples;
- criação idempotente;
- CRUD mínimo;
- testes.

## Passo 5

Criar dataset sintético:

- quatro seleções;
- vinte partidas;
- jogadores fictícios;
- técnicos fictícios;
- dados suficientes para testes.

## Passo 6

Criar ingestão:

- CSV;
- JSON;
- user report.

## Passo 7

Criar endpoints:

- `/teams`;
- `/matches`;
- `/user-reports`;
- `/rag/search`.

## Passo 8

Criar indexação Qdrant.

## Passo 9

Criar Elo.

## Passo 10

Criar página Streamlit mínima.

Não avançar para CatBoost antes de:

- dados;
- snapshots;
- leakage tests;
- Elo;
- Poisson;
- avaliação temporal.

---

# 33. Prompt inicial para colar no Opus

```text
Leia integralmente MASTER_PLAN.md.

Inicie apenas a Fase 0 — Fundação do repositório.

Antes de codificar:
1. proponha a estrutura final dos arquivos;
2. identifique decisões que devem entrar em DECISIONS.md;
3. liste os critérios de aceite da fase;
4. identifique riscos específicos de Windows 11, Docker Desktop e LM Studio.

Depois implemente a fase em pequenos passos.

Requisitos obrigatórios:
- Python 3.12;
- layout src;
- FastAPI;
- Typer;
- pytest;
- Ruff;
- mypy;
- pre-commit;
- GitHub Actions;
- Docker Compose com Qdrant;
- configuração via .env e YAML;
- logs estruturados;
- endpoint /health;
- comando copamind doctor;
- README com instalação Windows e Linux;
- nenhum segredo no repositório.

Ao terminar:
- execute os testes;
- execute lint;
- execute mypy;
- apresente a árvore de arquivos;
- atualize TASKS.md;
- registre decisões;
- documente os comandos usados;
- não avance para a Fase 1.
```

---

# 34. Prompt para a Fase 1

```text
Leia MASTER_PLAN.md, TASKS.md, DECISIONS.md e o código atual.

Implemente apenas a Fase 1 — Modelo de dados e ingestão de amostra.

Crie:
- schemas Pydantic;
- persistência DuckDB;
- criação idempotente de tabelas;
- importador CSV;
- importador JSON;
- dataset sintético legalmente redistribuível;
- validação Pandera;
- deduplicação básica;
- snapshot_id;
- source;
- collected_at;
- available_at;
- testes unitários e de integração;
- endpoints para listar seleções e partidas;
- documentação.

Não implemente ainda:
- CatBoost;
- simulador;
- LLM;
- MCP;
- frontend React.

Ao terminar, prove:
- ingestão reproduzível;
- deduplicação;
- rejeição de dados inválidos;
- consultas aos últimos jogos;
- ausência de segredos;
- testes e lint passando.
```

---

# 35. Melhorias futuras

- atualização automática de fontes;
- comparação com odds em modelo isolado;
- análise de sentimento;
- ingestão de PDFs;
- parser de notícias;
- fine-tuning QLoRA do auditor;
- geração automática de cards;
- narrador de simulações;
- plugin para VS Code;
- desktop app;
- suporte multilíngue;
- leaderboard de modelos;
- benchmarking comunitário;
- dataset de prompts;
- torneios adicionais;
- modo histórico para Copas anteriores;
- sistema de contribuição de dados;
- assinatura criptográfica de snapshots.

---

# 36. Resultado esperado

Ao final, o projeto deve permitir:

```text
Usuário pergunta:
“Quem tem mais chance de ganhar a Copa e por quê?”

O sistema:
1. identifica o snapshot;
2. consulta dados;
3. calcula probabilidades;
4. executa simulação;
5. recupera contexto;
6. chama o primeiro modelo;
7. descarrega;
8. chama o segundo modelo;
9. descarrega;
10. chama o auditor;
11. valida claims;
12. apresenta boxes independentes;
13. apresenta consenso;
14. mostra fontes, incertezas e dados ausentes;
15. salva a execução para reprodução futura.
```

O diferencial do CopaMind 2026 não será apenas indicar um possível campeão.

O diferencial será mostrar:

- de onde veio cada dado;
- qual modelo calculou cada probabilidade;
- como os modelos divergiram;
- quais informações estavam faltando;
- qual snapshot foi utilizado;
- como a resposta pode ser reproduzida.

---

# 37. Addendum v2 — Reavaliação e escopo ampliado

> Esta seção consolida as decisões tomadas na reavaliação do plano. Onde houver conflito com seções anteriores, **este addendum prevalece**. O backlog operacional detalhado está em `TASKS.md`; as decisões arquiteturais em `DECISIONS.md`; o cronograma em `ROADMAP.md`.

## 37.1 Objetivo estratégico

Projeto de portfólio para LinkedIn, com engajamento durante a Copa 2026 (final em 19/07/2026). Prioridade em entregar valor visível cedo (dashboard + bracket + cards + bolão) e transparência auditável como diferencial.

## 37.2 Reordenação de fases (slice vertical primeiro)

```text
E0 Fundação → E1 Dados → E3a Elo+forma → E4 Poisson → E4b Simulação MC →
E8a Dashboard+bracket+cards (MVP público) → E11 Bolão de IAs (live) →
E2 User reports → E5 RAG → E6 MCP → E7 LLMs+benchmark →
E3b CatBoost/XGBoost/ensemble/calibração → E8b UI completa bilíngue → E9 Publicação
```

## 37.3 Roster de LLMs locais para 8 GB VRAM (Q4, sequencial com unload)

| Papel | Modelo sugerido | Marca |
|---|---|---|
| Analista | Qwen3-8B | Alibaba |
| Auditor rápido / extração | Qwen3-4B | Alibaba |
| Analista alternativo | Gemma 3 12B (ou Gemma 4, a confirmar) | Google |
| Challenger | Llama 3.1 8B | Meta |
| Challenger | Ministral 8B / Mistral Nemo 12B | Mistral |
| Auditor pesado | Phi-4 (14B) | Microsoft |
| Challenger (reasoning) | DeepSeek-R1-Distill-Qwen-7B | DeepSeek |
| Embeddings | bge-m3 (multilíngue) | BAAI |
| Reranker | bge-reranker-v2-m3 | BAAI |

Regra: no máximo 1–2 modelos por marca; nomes fixados apenas em `models.yaml`, não no código.

## 37.4 Perfis de hardware (config-driven)

O mesmo código roda em 8 GB e 24 GB via **perfil de hardware** em `models.yaml`:

- `hardware_profile: 8gb` → roster acima, Q4, contexto 8–12k, execução **sempre sequencial**.
- `hardware_profile: 24gb` → modelos 27–32B (Gemma 3 27B, Qwen3-32B/30B-A3B, DeepSeek-R1-32B, Mixtral 8x7B), contexto 32k+, Q5/Q6/Q8 nos 8–14B, execução **concorrente opt-in** (default continua sequencial e reprodutível).

## 37.5 Machine learning como motor preditivo

O LLM interpreta/explica; **o ML produz as probabilidades** e nunca é sobrescrito pelo LLM. Adições ao plano original:

- SHAP / feature importance para explicabilidade;
- validação temporal walk-forward (além dos leakage tests);
- Optuna com objetivo em Brier/Log-Loss;
- quantificação de incerteza (bootstrap / distribuição Monte Carlo);
- **stacking com pesos aprendidos** em validação temporal (substitui os pesos fixos do §16.5);
- detecção de drift na Copa ao vivo.

## 37.6 Internacionalização (EN / PT-BR)

- PT-BR default, EN como segundo idioma; seletor no header, detecção via `Accept-Language`, persistência.
- Apenas a camada de apresentação é traduzida; **dados factuais e lineage permanecem canônicos** (`snapshot_id`, `evidence_ids`, códigos FIFA não são traduzidos).
- Respostas dos LLMs seguem o `response_language` da sessão (ver contrato §15.4).
- Formatação de números/datas por locale; disclaimer bilíngue.
- Cards de conteúdo gerados em PT-BR **e** EN.

## 37.7 Interface

- **Streamlit** para MVP interno/backtest; **Reflex** para a demo pública polida (mantém stack Python).
- Dashboard com: ranking de título, **árvore de mata-mata (bracket)**, evolução de probabilidade, radar head-to-head, **divergência entre LLMs**, curva de calibração, **aba Bolão**.

## 37.8 Orquestração

- **Pydantic AI** (encaixa em Pydantic v2) ou **LangGraph** para a máquina de estados do agente (§14.2).

## 37.9 Benchmark de LLMs como feature de primeira classe (E7)

Harness que pontua cada modelo local em: groundedness, aderência ao JSON Schema, concordância com o modelo estatístico, latência, tokens/s, VRAM real, tempo de load/unload — exposto como **leaderboard local** e exportável para conteúdo.

## 37.10 Bolão de IAs Locais (E11) — feature headline

A cada jogo da Copa, cada preditor (ensemble estatístico "a casa" + cada LLM local) registra um palpite **antes do apito**, travado com `snapshot_id` + `locked_at` (imutável). Após o jogo, ingere-se o resultado real e pontua-se cada preditor (pontos de bolão + Brier/Log-Loss). O leaderboard acumulado ao longo do torneio vira conteúdo recorrente.

Integridade temporal: palpites imutáveis pós-kickoff; resultado só entra depois; snapshot incremental atualiza forma/escalação para a próxima rodada. Novas tabelas: `pool_predictions`, `pool_results`, `pool_leaderboard`.

## 37.11 Fontes de dados abertas e redistribuíveis

OpenFootball, StatsBomb Open Data, football-data.org (tier grátis), Wikidata. Evitar scraping restrito por ToS (ex.: FBref).
