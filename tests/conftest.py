"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from copamind.api.app import create_app
from copamind.api.dependencies import get_repository
from copamind.core.config import Settings
from copamind.data.ingestion.service import ingest_samples
from copamind.data.repositories import DuckDBRepository


@pytest.fixture
def settings() -> Settings:
    """Configuração isolada para testes (não lê `.env` do disco)."""
    return Settings(_env_file=None, app_env="testing", log_json=False)  # type: ignore[call-arg]


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """Cliente de teste da API FastAPI."""
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded_repo() -> Iterator[DuckDBRepository]:
    """Repositório em memória populado com o dataset de amostra."""
    with DuckDBRepository(":memory:") as repo:
        ingest_samples(repo)
        yield repo


@pytest.fixture
def data_client(settings: Settings, seeded_repo: DuckDBRepository) -> Iterator[TestClient]:
    """Cliente de teste com o repositório de dados populado (via override)."""
    app = create_app(settings)
    app.dependency_overrides[get_repository] = lambda: seeded_repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
