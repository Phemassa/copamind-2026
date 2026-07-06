"""Configuração da aplicação via variáveis de ambiente e `.env`.

As configurações seguem o `.env.example`. Nenhum segredo é versionado
(ver DECISIONS ADR e MASTER_PLAN §28).
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    """Ambientes de execução suportados."""

    development = "development"
    testing = "testing"
    production = "production"


class HardwareProfile(StrEnum):
    """Perfis de hardware para LLMs locais (ver DECISIONS ADR-0003)."""

    vram_8gb = "8gb"
    vram_24gb = "24gb"


class Locale(StrEnum):
    """Idiomas suportados pela interface (ver DECISIONS ADR-0006)."""

    pt_br = "pt-BR"
    en = "en"


class Settings(BaseSettings):
    """Configuração central do CopaMind, carregada de ambiente e `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Aplicação
    app_env: AppEnv = AppEnv.development
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    # Armazenamento de dados
    duckdb_path: Path = Path("./data/copamind.duckdb")

    # Qdrant (RAG)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "copamind_knowledge"

    # LM Studio
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_api_key: str = "lm-studio"
    lmstudio_timeout_seconds: int = 300

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Perfil de hardware
    hardware_profile: HardwareProfile = HardwareProfile.vram_8gb

    # Modelos (overrides opcionais; IDs canônicos ficam em models.yaml)
    model_analyst_id: str = ""
    model_challenger_id: str = ""
    model_auditor_id: str = ""
    embedding_model_id: str = ""

    # i18n
    default_locale: Locale = Locale.pt_br

    # Observabilidade
    log_level: str = "INFO"
    log_json: bool = True

    # Snapshot
    default_snapshot_policy: str = "latest_consistent"

    @property
    def is_production(self) -> bool:
        """Indica se a aplicação está em ambiente de produção."""
        return self.app_env is AppEnv.production


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a instância singleton de :class:`Settings`."""
    return Settings()
