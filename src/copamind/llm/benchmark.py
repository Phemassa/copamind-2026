"""Benchmark de LLMs locais (E7, MASTER_PLAN §37.9).

Pontua cada modelo em aderência ao schema, groundedness, latência, tokens/s e
concordância com o modelo estatístico — base do leaderboard local.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from copamind.llm.client import LLMClient, LLMError, extract_json
from copamind.llm.contracts import AnalystResponse
from copamind.llm.orchestrator import _ANALYST_SYSTEM, EvidencePack, ModelSpec


class BenchmarkRow(BaseModel):
    """Métricas de um modelo em uma pergunta."""

    model_id: str
    role: str
    schema_valid: bool
    grounded_ratio: float = Field(ge=0, le=1)
    latency_ms: float = Field(ge=0)
    tokens_per_second: float | None = None
    agrees_with_statistical_model: bool | None = None
    error: str | None = None


def _grounded_ratio(response: AnalystResponse) -> float:
    if not response.claims:
        return 1.0
    return sum(1 for c in response.claims if c.evidence_ids) / len(response.claims)


def benchmark_models(
    client: LLMClient,
    specs: list[ModelSpec],
    question: str,
    evidence: EvidencePack,
    *,
    response_language: str = "pt-BR",
) -> list[BenchmarkRow]:
    """Executa cada modelo (sequencialmente, com unload) e coleta métricas."""
    rows: list[BenchmarkRow] = []
    for spec in specs:
        messages = [
            {
                "role": "system",
                "content": _ANALYST_SYSTEM.format(language=response_language),
            },
            {
                "role": "user",
                "content": f"Pergunta: {question}\n\nEvidências:\n{evidence.to_context()}",
            },
        ]
        row = BenchmarkRow(
            model_id=spec.model_id,
            role=spec.role,
            schema_valid=False,
            grounded_ratio=0.0,
            latency_ms=0.0,
        )
        try:
            raw = client.complete(
                messages=messages, model_id=spec.model_id, temperature=spec.temperature
            )
            row.latency_ms = raw.latency_ms
            row.tokens_per_second = raw.tokens_per_second
            response = AnalystResponse.model_validate(extract_json(raw.content))
            row.schema_valid = True
            row.grounded_ratio = _grounded_ratio(response)
            row.agrees_with_statistical_model = response.agrees_with_statistical_model
        except (LLMError, ValidationError) as exc:
            row.error = str(exc)
        finally:
            if spec.unload_after_run:
                client.unload(spec.model_id)
        rows.append(row)
    return rows
