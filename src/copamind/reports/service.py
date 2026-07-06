"""Serviço de relatos do usuário: criação, versionamento, verificação e exclusão.

Regras (MASTER_PLAN §11): dados entram como `user_input`, `verified=false`;
correções geram novas versões (histórico preservado); nunca são promovidos
automaticamente ao treino oficial.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import UserReport
from copamind.reports.extractors import Extractor, RuleBasedExtractor


def _now() -> datetime:
    return datetime.now(UTC)


def create_user_report(
    repo: DuckDBRepository,
    text: str,
    *,
    session_id: str | None = None,
    extractor: Extractor | None = None,
) -> UserReport:
    """Cria um relato (versão 1) a partir de texto livre."""
    extractor = extractor or RuleBasedExtractor()
    extracted = extractor.extract(text)
    now = _now()
    report = UserReport(
        report_id=str(uuid.uuid4()),
        version=1,
        is_current=True,
        deleted=False,
        session_id=session_id,
        user_text=text,
        report_type=extracted.report_type,
        parsed_payload=extracted.parsed_payload,
        entities=extracted.entities,
        source_type="user_input",
        verified=False,
        confidence=extracted.confidence,
        created_at=now,
        available_at=now,
        snapshot_id=repo.latest_snapshot_id() or "adhoc",
    )
    repo.insert_user_report(report)
    return report


def update_user_report(
    repo: DuckDBRepository,
    report_id: str,
    text: str,
    *,
    extractor: Extractor | None = None,
) -> UserReport | None:
    """Corrige um relato criando uma nova versão (mantém o histórico)."""
    current = repo.get_user_report(report_id)
    if current is None:
        return None
    extractor = extractor or RuleBasedExtractor()
    extracted = extractor.extract(text)
    new_version = current.version + 1
    updated = current.model_copy(
        update={
            "version": new_version,
            "is_current": True,
            "user_text": text,
            "report_type": extracted.report_type,
            "parsed_payload": extracted.parsed_payload,
            "entities": extracted.entities,
            "confidence": extracted.confidence,
            "verified": False,
            "created_at": _now(),
        }
    )
    repo.add_user_report_version(updated)
    return updated


def verify_user_report(repo: DuckDBRepository, report_id: str) -> UserReport | None:
    """Marca um relato como verificado (nova versão)."""
    current = repo.get_user_report(report_id)
    if current is None:
        return None
    verified = current.model_copy(
        update={"version": current.version + 1, "verified": True, "created_at": _now()}
    )
    repo.add_user_report_version(verified)
    return verified


def delete_user_report(repo: DuckDBRepository, report_id: str) -> bool:
    """Exclui um relato via tombstone (nova versão marcada como deletada)."""
    current = repo.get_user_report(report_id)
    if current is None:
        return False
    tombstone = current.model_copy(
        update={"version": current.version + 1, "deleted": True, "created_at": _now()}
    )
    repo.add_user_report_version(tombstone)
    return True
