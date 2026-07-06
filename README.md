# CopaMind 2026 🧠⚽

> Plataforma **local** e **open source** de inteligência esportiva: coleta dados de futebol, treina modelos preditivos locais, simula a Copa 2026 milhares de vezes e responde perguntas via chat com RAG, MCP e múltiplos LLMs locais executados em sequência — sempre com **transparência e reprodutibilidade**.

**Aviso:** projeto sem vínculo oficial com FIFA, seleções, federações ou organizadores. As probabilidades são **experimentais e educacionais**, não representam garantia de resultado e não incentivam apostas.

---

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

## Desenvolvimento

```bash
pre-commit install     # hooks de qualidade
ruff check .           # lint
ruff format .          # formatação
mypy                   # tipos
pytest                 # testes + cobertura
```

## Estado do projeto

Fase 0 (fundação) concluída: estrutura, configuração, logging estruturado, API `/health` e `/ready`, CLI `copamind doctor`, Docker Compose do Qdrant, lint/tipos/testes e CI. Próximas fases no [ROADMAP.md](ROADMAP.md).

## Licença

[MIT](LICENSE).
