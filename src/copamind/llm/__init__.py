"""Orquestração de LLMs locais (E7, MASTER_PLAN §15)."""

from copamind.llm.client import FakeLLMClient, LLMClient, LLMError, LLMResponse
from copamind.llm.contracts import (
    AnalystResponse,
    AuditorResponse,
    Claim,
    ClaimVerdict,
    ConsensusResponse,
    SupportingFactor,
)
from copamind.llm.orchestrator import (
    EvidencePack,
    ModelBox,
    ModelSpec,
    OrchestrationResult,
    SequentialOrchestrator,
    build_evidence_pack,
)

__all__ = [
    "AnalystResponse",
    "AuditorResponse",
    "Claim",
    "ClaimVerdict",
    "ConsensusResponse",
    "EvidencePack",
    "FakeLLMClient",
    "LLMClient",
    "LLMError",
    "LLMResponse",
    "ModelBox",
    "ModelSpec",
    "OrchestrationResult",
    "SequentialOrchestrator",
    "SupportingFactor",
    "build_evidence_pack",
]
