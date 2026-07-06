"""Aplicação CLI do CopaMind (Typer)."""

from __future__ import annotations

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from copamind import __version__
from copamind.cli.doctor import CheckStatus, has_failures, run_diagnostics
from copamind.core.config import get_settings
from copamind.data.ingestion.service import (
    ingest_matches_file,
    ingest_samples,
    ingest_teams_file,
)
from copamind.data.repositories import DuckDBRepository

app = typer.Typer(
    name="copamind",
    help="CopaMind 2026 — inteligência esportiva local para a Copa 2026.",
    no_args_is_help=True,
    add_completion=False,
)

api_app = typer.Typer(help="Comandos da API.")
app.add_typer(api_app, name="api")

ingest_app = typer.Typer(help="Comandos de ingestão de dados.")
app.add_typer(ingest_app, name="ingest")

console = Console()

_STATUS_STYLE = {
    CheckStatus.ok: "green",
    CheckStatus.warn: "yellow",
    CheckStatus.fail: "red",
}


@app.command()
def version() -> None:
    """Exibe a versão do CopaMind."""
    console.print(f"CopaMind [bold cyan]{__version__}[/]")


@app.command()
def doctor() -> None:
    """Verifica o ambiente (Python, dependências, configs, serviços locais)."""
    results = run_diagnostics()

    table = Table(title="CopaMind — Diagnóstico do ambiente")
    table.add_column("Verificação", style="bold")
    table.add_column("Status")
    table.add_column("Detalhe")

    for result in results:
        style = _STATUS_STYLE[result.status]
        table.add_row(result.name, f"[{style}]{result.status.value}[/]", result.detail)

    console.print(table)

    if has_failures(results):
        console.print("[red]Há falhas críticas. Corrija antes de prosseguir.[/]")
        raise typer.Exit(code=1)
    console.print("[green]Ambiente pronto.[/] Avisos (WARN) são opcionais na Fase 0.")


@api_app.command("serve")
def api_serve(
    host: str | None = typer.Option(None, help="Host de bind (padrão: config)."),
    port: int | None = typer.Option(None, help="Porta de bind (padrão: config)."),
    reload: bool = typer.Option(False, help="Recarregar em mudanças (desenvolvimento)."),
) -> None:
    """Sobe a API FastAPI com Uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "copamind.api.app:app",
        host=host or settings.app_host,
        port=port or settings.app_port,
        reload=reload,
    )


@ingest_app.command("sample")
def ingest_sample() -> None:
    """Ingere o dataset sintético de amostra na base DuckDB."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        result = ingest_samples(repo)
    console.print(
        f"[green]Ingestão concluída.[/] Times: {result.teams}, "
        f"Partidas: {result.matches}, Snapshot: {result.snapshot_id}"
    )


@ingest_app.command("file")
def ingest_file(
    path: str = typer.Argument(..., help="Caminho do arquivo JSON/CSV."),
    entity: str = typer.Option(..., help="Tipo de entidade: 'teams' ou 'matches'."),
) -> None:
    """Ingere seleções ou partidas de um arquivo JSON/CSV."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        if entity == "teams":
            count = ingest_teams_file(repo, path)
        elif entity == "matches":
            count = ingest_matches_file(repo, path)
        else:
            console.print("[red]entity deve ser 'teams' ou 'matches'.[/]")
            raise typer.Exit(code=1)
    console.print(f"[green]Ingeridos {count} registros de '{entity}'.[/]")


if __name__ == "__main__":
    app()
