"""Contratos de saída estruturada dos LLMs (MASTER_PLAN §15.4).

Todo claim factual deve vir acompanhado de `evidence_ids` (regra de grounding,
§15.5). O idioma da resposta segue `response_language` (DECISIONS ADR-0006).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]
ClaimStatus = Literal[
    "supported",
    "partially_supported",
    "not_supported",
    "contradictory",
    "outdated",
]


class SupportingFactor(BaseModel):
    """Fator que sustenta a análise, com evidências."""

    factor: str
    evidence_ids: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    """Afirmação factual com as evidências que a sustentam."""

    text: str
    evidence_ids: list[str] = Field(default_factory=list)


class AnalystResponse(BaseModel):
    """Resposta estruturada de um analista/challenger."""

    model_role: str
    response_language: str = "pt-BR"
    answer: str
    predicted_team: str | None = None
    confidence: Confidence = "medium"
    supporting_factors: list[SupportingFactor] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    agrees_with_statistical_model: bool = True


class ClaimVerdict(BaseModel):
    """Veredito do auditor sobre um claim."""

    text: str
    status: ClaimStatus


class AuditorResponse(BaseModel):
    """Resposta estruturada do auditor de evidências."""

    model_role: str = "evidence_auditor"
    response_language: str = "pt-BR"
    verdicts: list[ClaimVerdict] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    notes: str = ""


class ConsensusResponse(BaseModel):
    """Síntese final auditável a partir das respostas dos modelos."""

    answer: str
    predicted_team: str | None = None
    agreements: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
