"""Rotas de relatos do usuário (MASTER_PLAN §20)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from copamind.api.dependencies import get_repository
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import UserReport
from copamind.reports.service import (
    create_user_report,
    delete_user_report,
    update_user_report,
    verify_user_report,
)

router = APIRouter(tags=["user-reports"], prefix="/user-reports")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


class UserReportRequest(BaseModel):
    """Corpo para criar/atualizar um relato."""

    text: str
    session_id: str | None = None


@router.post("", response_model=UserReport, status_code=201)
def create(request: UserReportRequest, repo: RepoDep) -> UserReport:
    """Cria um relato a partir de texto livre."""
    return create_user_report(repo, request.text, session_id=request.session_id)


@router.get("", response_model=list[UserReport])
def list_reports(repo: RepoDep) -> list[UserReport]:
    """Lista os relatos atuais (não deletados)."""
    return repo.list_user_reports()


@router.get("/{report_id}", response_model=UserReport)
def get_report(report_id: str, repo: RepoDep) -> UserReport:
    """Retorna um relato pelo id."""
    report = repo.get_user_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


@router.patch("/{report_id}", response_model=UserReport)
def update(report_id: str, request: UserReportRequest, repo: RepoDep) -> UserReport:
    """Corrige um relato (gera nova versão)."""
    updated = update_user_report(repo, report_id, request.text)
    if updated is None:
        raise HTTPException(status_code=404, detail="report not found")
    return updated


@router.delete("/{report_id}", status_code=204)
def delete(report_id: str, repo: RepoDep) -> None:
    """Exclui um relato (tombstone; histórico preservado)."""
    if not delete_user_report(repo, report_id):
        raise HTTPException(status_code=404, detail="report not found")


@router.post("/{report_id}/verify", response_model=UserReport)
def verify(report_id: str, repo: RepoDep) -> UserReport:
    """Marca um relato como verificado."""
    verified = verify_user_report(repo, report_id)
    if verified is None:
        raise HTTPException(status_code=404, detail="report not found")
    return verified
