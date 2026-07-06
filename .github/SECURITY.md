# Política de Segurança / Security Policy

## Versões suportadas

O projeto está em fase alpha; apenas o branch `main` recebe correções.

## Reportando vulnerabilidades

Não abra uma issue pública para vulnerabilidades. Em vez disso, use o canal
privado de **Security Advisories** do GitHub deste repositório.

Please do not open public issues for security vulnerabilities. Use the private
**GitHub Security Advisories** channel of this repository instead.

Inclua: descrição, passos para reproduzir, impacto e, se possível, uma correção.

## Boas práticas adotadas

- Nenhum segredo é versionado (`.env`, chaves de API ficam fora do Git).
- Conteúdo recuperado (RAG) é tratado como **não confiável** (proteção contra prompt injection).
- Sem SQL/shell arbitrário a partir do LLM; ferramentas MCP separam read-only de escrita.
- Validação de entradas com Pydantic; `bandit` e `pip-audit` no CI.
