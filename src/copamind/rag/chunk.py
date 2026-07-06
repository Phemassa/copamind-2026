"""Chunks e metadados do RAG (MASTER_PLAN §12.3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from copamind.data.schemas import UserReport


class RagChunk(BaseModel):
    """Fragmento indexável com metadados de recuperação e linhagem."""

    chunk_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    entity_type: str = "user_report"
    team_ids: list[str] = Field(default_factory=list)
    source: str = "user_input"
    source_type: str = "user_input"
    verified: bool = False
    confidence: float = Field(default=0.0, ge=0, le=1)
    document_date: datetime | None = None
    snapshot_id: str = "adhoc"
    language: str = "pt-BR"
    tags: list[str] = Field(default_factory=list)


def chunk_user_report(report: UserReport) -> RagChunk:
    """Converte um relato do usuário em um chunk indexável."""
    return RagChunk(
        chunk_id=f"{report.report_id}:{report.version}",
        document_id=report.report_id,
        text=report.user_text,
        entity_type=f"user_report:{report.report_type}",
        team_ids=[str(e) for e in report.entities],
        source="user_input",
        source_type=report.source_type,
        verified=report.verified,
        confidence=report.confidence,
        document_date=report.created_at,
        snapshot_id=report.snapshot_id,
        tags=[str(report.report_type)],
    )
