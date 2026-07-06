# Contributing to CopaMind 2026

Obrigado pelo interesse em contribuir! / Thanks for your interest in contributing!

## Fluxo de trabalho

1. Abra uma issue descrevendo a mudança (bug, feature, fonte de dados).
2. Faça um fork e crie um branch a partir de `develop`:
   - `feature/<descrição>`, `fix/<descrição>` ou `docs/<descrição>`.
3. Garanta qualidade antes do PR:
   ```bash
   ruff check .
   ruff format --check .
   mypy
   pytest
   ```
4. Use **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `build:`, `ci:`, `chore:`).
5. Abra o PR para `develop` preenchendo o template.

## Definição de pronto

- Implementação + testes + documentação atualizados.
- `ruff`, `mypy` e `pytest` verdes.
- Erros tratados e logs presentes; nenhum segredo versionado.
- `TASKS.md` atualizado; decisões relevantes em `DECISIONS.md`.

## Princípios do projeto

- As probabilidades vêm dos **modelos estatísticos/ML** — o LLM interpreta e explica, nunca sobrescreve.
- Todo dado carrega linhagem (origem, coleta, disponibilidade, snapshot).
- Sem vazamento temporal: use `available_at`/`as_of`.
- Componentes locais e open source por padrão.

## Ambiente

Python 3.12. Instale com `pip install -e ".[data,dev]"`. Veja o [README](../README.md).
