# Arquitetura — CopaMind 2026

> Documento vivo. Descreve a arquitetura de alto nível, os módulos e os fluxos de dados do CopaMind 2026.
> Diagramas em [Mermaid](https://mermaid.js.org/) — renderizam automaticamente no GitHub e no VS Code.

**Princípio central:** o LLM **não produz** a probabilidade. As probabilidades vêm de modelos estatísticos/ML calibrados (Elo, Poisson/Dixon-Coles, ensemble, Monte Carlo). Os LLMs apenas **interpretam, consultam e explicam** — sempre com linhagem e reprodutibilidade.

---

## 1. Visão geral em camadas

```mermaid
flowchart TB
    subgraph SRC["Fontes de dados"]
        A1[APIs esportivas]
        A2["Arquivos CSV / JSON / Parquet"]
        A3[Fontes oficiais]
        A4["Relatos do usuário"]
    end

    subgraph ING["Camada de ingestão — data/"]
        B1["Connectors\n(data/connectors)"]
        B2["Ingestão + dedup\n(data/ingestion)"]
        B3["Validação + schemas\n(data/validation, schemas.py)"]
    end

    subgraph STORE["Armazenamento local"]
        C1[("Data lake\nraw / bronze / silver / gold\nDuckDB + Parquet")]
        C2[("Base textual\ndocumentos + metadados")]
        C3[("Qdrant\nembeddings vetoriais")]
    end

    subgraph FEAT["Features — features/"]
        D1["Forma recente\n(form.py)"]
        D2["Força ofensiva/defensiva\n(service.py)"]
    end

    subgraph MODELS["Modelos preditivos — models/"]
        E1[Elo]
        E2["Poisson / Dixon-Coles"]
        E3["Ensemble + Calibração\n(isotônica, Brier/LogLoss/ECE)"]
    end

    subgraph SIM["Simulação — simulation/"]
        F1["Monte Carlo do torneio\nchances por fase e título"]
    end

    subgraph RAG["RAG — rag/"]
        G1["Chunking + Embeddings"]
        G2["Retriever híbrido\n(vetorial + léxico)"]
        G3["Service + anti prompt-injection"]
    end

    subgraph AGENT["Agente + orquestração"]
        H1["MCP tools\n(mcp/)"]
        H2["Orquestrador de LLMs locais\n(llm/)\nanalista → challenger → auditor → consenso"]
    end

    subgraph IFACE["Interfaces"]
        I1["API FastAPI\n(api/)"]
        I2["CLI copamind\n(cli/)"]
        I3["Dashboard Streamlit EN/PT-BR\n(ui/, apps/streamlit)"]
        I4["Servidor MCP\n(copamind-mcp)"]
    end

    SRC --> ING
    B1 --> B2 --> B3
    B3 --> C1
    B3 --> C2
    C2 --> C3

    C1 --> FEAT
    D1 --> D2 --> MODELS
    E1 --> E3
    E2 --> E3
    E3 --> SIM

    C3 --> G1 --> G2 --> G3
    C1 --> G2

    SIM --> H1
    E3 --> H1
    G3 --> H1
    H1 --> H2

    H2 --> IFACE
    SIM --> I1
    E3 --> I1
    G3 --> I1
    I1 --> I3
```

---

## 2. Fluxo de uma previsão (pipeline preditivo)

Separa claramente **dados estruturados** (probabilidades) de **dados textuais** (explicação via RAG/LLM).

```mermaid
flowchart LR
    RAW["Dados brutos\n(raw)"] --> VAL["Validação\n+ dedup"]
    VAL --> LAKE[("Data lake\nsilver/gold")]
    LAKE --> FE["Feature engineering\nforma / força / contexto"]
    FE --> M1[Elo]
    FE --> M2["Poisson / Dixon-Coles"]
    M1 --> ENS[Ensemble]
    M2 --> ENS
    ENS --> CAL["Calibração\nisotônica"]
    CAL --> PROB["Probabilidades\nV / E / D + placares"]
    PROB --> MC["Simulação\nMonte Carlo"]
    MC --> OUT["Chances por fase\ne de título"]

    PROB -.linhagem.-> LIN["snapshot_id, versões,\nseed, origem, timestamp"]
    OUT -.linhagem.-> LIN
```

---

## 3. Orquestração sequencial de LLMs locais

Restrição de hardware (8 GB VRAM): os modelos rodam **um de cada vez**, com *unload* entre eles. O LLM nunca gera a probabilidade — ele consome os resultados dos modelos + RAG e produz interpretação auditável.

```mermaid
sequenceDiagram
    participant U as Usuário (chat)
    participant O as Orquestrador (llm/)
    participant MCP as MCP tools
    participant M as Modelos + Simulação
    participant R as RAG (Qdrant)
    participant L as LLM local (LM Studio/Ollama)

    U->>O: Pergunta
    O->>MCP: Consulta ferramentas
    MCP->>M: Probabilidades / simulação
    MCP->>R: Documentos relevantes
    M-->>O: Dados estruturados
    R-->>O: Evidências textuais

    Note over O,L: Execução sequencial (unload entre modelos)
    O->>L: 1) Analista
    L-->>O: Resposta A
    O->>L: 2) Challenger (2ª opinião)
    L-->>O: Resposta B
    O->>L: 3) Auditor
    L-->>O: Verificação
    O->>U: Consenso final + snapshot + evidências
```

---

## 4. Mapa de módulos (`src/copamind/`)

| Módulo | Responsabilidade |
|--------|------------------|
| `core/` | Configuração (`config.py`) e logging estruturado (`logging.py`) |
| `data/` | Connectors, ingestão, validação, schemas e repositórios (DuckDB/Parquet) |
| `features/` | Forma recente e força ofensiva/defensiva pré-jogo |
| `models/` | `elo/`, `poisson/`, `ensemble/`, `calibration/` |
| `simulation/` | Simulação Monte Carlo do torneio |
| `rag/` | Chunking, embeddings, retriever híbrido, store (Qdrant) e service |
| `llm/` | Cliente, contratos, hardware, orquestrador e benchmark de LLMs locais |
| `mcp/` | Servidor MCP e ferramentas expostas ao agente/IDE |
| `pool/` | Bolão de IAs locais: preditores, scoring e leaderboard |
| `content/` | Cards e conteúdo derivado |
| `reports/` | Relatórios e extratores |
| `api/` | FastAPI: rotas `health`, `data`, `predictions`, `simulations`, `rag`, `chat`, `pool`, `user_reports` |
| `cli/` | Comando `copamind` (`main.py`, `doctor.py`) |
| `ui/` | Dashboard bilíngue (EN/PT-BR) em Streamlit |

---

## 5. Superfícies de interface

```mermaid
flowchart LR
    CORE["Núcleo\nmodelos + simulação + RAG + LLM"]
    CORE --> API["API FastAPI\n/health /predictions /simulations\n/rag /chat /pool /data"]
    CORE --> CLI["CLI\ncopamind doctor / ingest / api / ui"]
    CORE --> MCP["Servidor MCP\ncopamind-mcp (read-only + escrita)"]
    API --> UI["Dashboard Streamlit\nEN / PT-BR"]
```

---

## 6. Reprodutibilidade e linhagem

Todo resultado (previsão, simulação ou resposta de chat) registra:

- `snapshot_id` e versão do dataset;
- versão das features e do modelo;
- parâmetros e `seed`;
- data/hora e origem dos dados;
- LLMs utilizados, prompts e documentos recuperados;
- tempos de execução.

Isso garante que qualquer resposta possa ser **auditada e reproduzida** — princípio inegociável do projeto.

---

## Referências

- Plano completo: [CopaMind_2026_MASTER_PLAN.md](CopaMind_2026_MASTER_PLAN.md)
- Decisões arquiteturais: [DECISIONS.md](DECISIONS.md)
- Backlog: [TASKS.md](TASKS.md) · Cronograma: [ROADMAP.md](ROADMAP.md)
