"""Testes dos perfis de hardware (E10)."""

from __future__ import annotations

from copamind.llm.hardware import (
    HardwareProfile,
    get_hardware_profile,
    load_hardware_profiles,
    suggest_profile,
)


def test_load_profiles_from_example() -> None:
    profiles = load_hardware_profiles("config/models.example.yaml")
    assert "8gb" in profiles
    assert "24gb" in profiles
    assert profiles["8gb"].execution == "sequential"


def test_get_profile() -> None:
    profile = get_hardware_profile("24gb", "config/models.example.yaml")
    assert profile is not None
    assert profile.default_context_length >= 8192


def test_suggest_profile_thresholds() -> None:
    assert suggest_profile(8.0) == "8gb"
    assert suggest_profile(None) == "8gb"
    assert suggest_profile(24.0) == "24gb"
    assert suggest_profile(20.0) == "24gb"


def test_profile_concurrency_flag() -> None:
    seq = HardwareProfile(name="8gb", max_concurrent_models=1, execution="sequential")
    conc = HardwareProfile(name="24gb", max_concurrent_models=2, execution="concurrent")
    assert seq.allows_concurrency is False
    assert conc.allows_concurrency is True

