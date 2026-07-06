"""Testes de configuração."""

from __future__ import annotations

from pathlib import Path

from copamind.core.config import AppEnv, HardwareProfile, Locale, Settings


def test_defaults() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.app_env is AppEnv.development
    assert settings.app_port == 8000
    assert settings.hardware_profile is HardwareProfile.vram_8gb
    assert settings.default_locale is Locale.pt_br
    assert settings.is_production is False


def test_env_override(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_PORT", "9001")
    monkeypatch.setenv("HARDWARE_PROFILE", "24gb")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.app_env is AppEnv.production
    assert settings.app_port == 9001
    assert settings.hardware_profile is HardwareProfile.vram_24gb
    assert settings.is_production is True


def test_duckdb_path_is_path() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert isinstance(settings.duckdb_path, Path)


