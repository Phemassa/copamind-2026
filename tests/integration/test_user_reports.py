"""Testes de integração dos relatos do usuário (serviço + API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from copamind.data.repositories import DuckDBRepository
from copamind.reports.service import (
    create_user_report,
    delete_user_report,
    update_user_report,
    verify_user_report,
)

_TEXT = "O Brasil venceu o México por 2 a 1 ontem."


def test_create_and_get(seeded_repo: DuckDBRepository) -> None:
    report = create_user_report(seeded_repo, _TEXT)
    assert report.source_type == "user_input"
    assert report.verified is False
    fetched = seeded_repo.get_user_report(report.report_id)
    assert fetched is not None
    assert fetched.version == 1


def test_update_creates_new_version(seeded_repo: DuckDBRepository) -> None:
    report = create_user_report(seeded_repo, _TEXT)
    updated = update_user_report(
        seeded_repo, report.report_id, "O Brasil venceu o México por 3 a 0."
    )
    assert updated is not None
    assert updated.version == 2
    # Histórico preservado: duas versões existem, uma corrente.
    assert seeded_repo.count("user_reports") == 2
    current = seeded_repo.get_user_report(report.report_id)
    assert current is not None
    assert current.parsed_payload["home_score"] == 3


def test_verify(seeded_repo: DuckDBRepository) -> None:
    report = create_user_report(seeded_repo, _TEXT)
    verified = verify_user_report(seeded_repo, report.report_id)
    assert verified is not None
    assert verified.verified is True
    assert verified.version == 2


def test_delete_is_tombstone(seeded_repo: DuckDBRepository) -> None:
    report = create_user_report(seeded_repo, _TEXT)
    assert delete_user_report(seeded_repo, report.report_id) is True
    assert seeded_repo.get_user_report(report.report_id) is None
    # Histórico preservado (versão original + tombstone).
    assert seeded_repo.count("user_reports") == 2


def test_not_promoted_to_training(seeded_repo: DuckDBRepository) -> None:
    matches_before = seeded_repo.count("matches")
    create_user_report(seeded_repo, _TEXT)
    # Relato do usuário não vira partida no conjunto oficial.
    assert seeded_repo.count("matches") == matches_before


def test_user_report_api(data_client: TestClient) -> None:
    created = data_client.post("/user-reports", json={"text": _TEXT})
    assert created.status_code == 201
    report_id = created.json()["report_id"]

    listed = data_client.get("/user-reports")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patched = data_client.patch(
        f"/user-reports/{report_id}", json={"text": "O Brasil venceu o México por 4 a 0."}
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2

    verified = data_client.post(f"/user-reports/{report_id}/verify")
    assert verified.status_code == 200
    assert verified.json()["verified"] is True

    deleted = data_client.delete(f"/user-reports/{report_id}")
    assert deleted.status_code == 204
    assert data_client.get(f"/user-reports/{report_id}").status_code == 404

