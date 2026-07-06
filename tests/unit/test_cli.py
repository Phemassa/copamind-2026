"""Testes do diagnóstico e da CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from copamind.cli.doctor import CheckResult, CheckStatus, has_failures, run_diagnostics
from copamind.cli.main import app
from copamind.core.config import Settings

runner = CliRunner()


def test_run_diagnostics_includes_core_checks() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    results = run_diagnostics(settings)
    names = {r.name for r in results}
    assert {"Python", "Dependências", "Disco"}.issubset(names)


def test_python_and_dependencies_pass() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    results = {r.name: r for r in run_diagnostics(settings)}
    assert results["Python"].status is CheckStatus.ok
    assert results["Dependências"].status is CheckStatus.ok


def test_has_failures() -> None:
    ok = [CheckResult("a", CheckStatus.ok, "")]
    bad = [CheckResult("a", CheckStatus.fail, "")]
    assert has_failures(ok) is False
    assert has_failures(bad) is True


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "CopaMind" in result.stdout


def test_doctor_command_runs() -> None:
    # Serviços externos ausentes geram WARN, não FAIL, então exit_code == 0.
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Diagnóstico" in result.stdout


