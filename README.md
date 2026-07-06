# CopaMind 2026 🧠⚽

[![CI](https://github.com/Phemassa/copamind-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/Phemassa/copamind-2026/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Plataforma **local** e **open source** de inteligência esportiva: coleta dados de futebol, treina modelos preditivos locais, simula a Copa 2026 milhares de vezes e responde perguntas via chat com RAG, MCP e múltiplos LLMs locais executados em sequência — sempre com **transparência e reprodutibilidade**.

**Aviso:** projeto sem vínculo oficial com FIFA, seleções, federações ou organizadores. As probabilidades são **experimentais e educacionais**, não representam garantia de resultado e não incentivam apostas.

---

## Recursos

- 📊 **Modelos preditivos**: Elo, Poisson/Dixon-Coles, ensemble e calibração isotônica (Brier/Log-Loss/ECE)
- 🎲 **Simulação Monte Carlo** do torneio (chances por fase e de título), reprodutível por seed
- 🏆 **Bolão de IAs Locais**: preditores competem com palpites imutáveis e leaderboard (backtest anti-leakage)
- 🔍 **RAG** com busca híbrida (vetorial + léxico) e proteção contra prompt injection
- 🤖 **Orquestração de LLMs locais** (LM Studio/Ollama): analista → challenger → auditor → consenso + **benchmark**
- 🔌 **MCP** (`copamind-mcp`): ferramentas read-only e de escrita para o agente/IDE
- 🖥️ **Dashboard bilíngue (EN/PT-BR)** em Streamlit: ranking, previsões, bolão, calibração e chat
- 🧾 **Linhagem e reprodutibilidade** em cada resultado (origem, snapshot, evidências)

## Diferencial

Não é um chatbot que "chuta" o campeão. As probabilidades vêm de **modelos de ML calibrados** (Elo, Poisson, CatBoost, ensemble, Monte Carlo); os LLMs apenas **interpretam, consultam e explicam**. Cada resposta registra de onde veio o dado, qual modelo calculou, onde os modelos divergiram e qual snapshot foi usado.

Veja o plano completo em [CopaMind_2026_MASTER_PLAN.md](CopaMind_2026_MASTER_PLAN.md), o backlog em [TASKS.md](TASKS.md), as decisões em [DECISIONS.md](DECISIONS.md) e o cronograma em [ROADMAP.md](ROADMAP.md).

## Hardware recomendado

- Windows 11 (também roda em Linux), Docker Desktop, VS Code
- Python 3.12
- GPU NVIDIA com **8 GB de VRAM** (RTX 5070 Laptop) — evolução para servidor **24 GB** já prevista (perfis de hardware)
- 32 GB de RAM
- LM Studio e/ou Ollama para os LLMs locais

## Instalação

### Windows (PowerShell)

```powershell
git clone https://github.com/Phemassa/copamind-2026.git
cd copamind-2026
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[data,dev]"
Copy-Item .env.example .env
```

### Linux / macOS (bash)

```bash
git clone https://github.com/Phemassa/copamind-2026.git
cd copamind-2026
python -m venv .venv
source .venv/bin/activate
pip install -e ".[data,dev]"
cp .env.example .env
```

## Uso rápido

```bash
# Verificar o ambiente (Python, dependências, configs, serviços locais)
copamind doctor

# Subir o Qdrant (RAG) via Docker
docker compose -f docker/compose.yaml up -d

# Subir a API
copamind api serve
# health check:
curl http://127.0.0.1:8000/health
```

## Dashboard

```bash
copamind ingest sample     # carrega o dataset de exemplo
pip install -e ".[ui]"      # instala Streamlit/Plotly
copamind ui serve          # abre o dashboard bilíngue (EN/PT-BR)
```

## Desenvolvimento

```bash
pre-commit install     # hooks de qualidade
ruff check .           # lint
ruff format .          # formatação
mypy                   # tipos
pytest                 # testes + cobertura
```

## Estado do projeto

Núcleo entregue (145 testes verdes): dados/ingestão (E1), user reports (E2), Elo + forma (E3a), Poisson/Dixon-Coles (E4), ensemble + calibração (E3b), simulação Monte Carlo (E4b), RAG (E5), MCP (E6), orquestração de LLMs + benchmark (E7), dashboard bilíngue + chat (E8a/E8b) e Bolão de IAs (E11). Veja [TASKS.md](TASKS.md) e o [ROADMAP.md](ROADMAP.md).

## Conteúdo para divulgação

```bash
copamind content ranking --locale pt-BR   # card de chances de título (Markdown)
copamind content match --home T-NTL --away T-SDR --locale en
```

## Dados reais (OpenFootball)

```bash
# Baixe um worldcup.json de https://github.com/openfootball/worldcup.json
copamind ingest worldcup caminho/para/worldcup.json
```

## Contribuição e segurança

- [CONTRIBUTING](.github/CONTRIBUTING.md) · [SECURITY](.github/SECURITY.md) · [MODEL_CARD](MODEL_CARD.md)
- Conventional Commits; qualidade obrigatória (`ruff`, `mypy`, `pytest`) antes do PR.

## Licença

[MIT](LICENSE).
