"""Aplicação CLI do CopaMind (Typer)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
from copamind.features.service import build_elo
from copamind.llm.benchmark import benchmark_models
from copamind.llm.client import LMStudioClient
from copamind.llm.config import load_model_specs
from copamind.llm.orchestrator import build_evidence_pack
from copamind.models.poisson.service import build_poisson
from copamind.pool.service import run_backtest
from copamind.simulation.service import build_default_config, run_simulation

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

train_app = typer.Typer(help="Comandos de treino/cálculo de modelos.")
app.add_typer(train_app, name="train")

ui_app = typer.Typer(help="Comandos da interface.")
app.add_typer(ui_app, name="ui")

pool_app = typer.Typer(help="Comandos do Bolão de IAs.")
app.add_typer(pool_app, name="pool")

llm_app = typer.Typer(help="Comandos de LLMs locais.")
app.add_typer(llm_app, name="llm")

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


@train_app.command("elo")
def train_elo() -> None:
    """Calcula os ratings Elo a partir das partidas finalizadas na base."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        repo.create_schema()
        elo = build_elo(repo)
        teams = repo.list_teams()

    table = Table(title="Ratings Elo")
    table.add_column("Seleção", style="bold")
    table.add_column("Elo", justify="right")
    ranked = sorted(teams, key=lambda t: elo.rating(t.team_id), reverse=True)
    for team in ranked:
        table.add_row(team.name, f"{elo.rating(team.team_id):.1f}")
    console.print(table)


@train_app.command("poisson")
def train_poisson() -> None:
    """Ajusta o modelo Poisson e exibe as forças de ataque/defesa por seleção."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        repo.create_schema()
        model = build_poisson(repo)
        teams = repo.list_teams()

    table = Table(title="Forças Poisson (ataque / defesa)")
    table.add_column("Seleção", style="bold")
    table.add_column("Ataque", justify="right")
    table.add_column("Defesa", justify="right")
    for team in teams:
        attack = model.attack_strength(team.team_id)
        defense = model.defense_strength(team.team_id)
        table.add_row(team.name, f"{attack:.2f}", f"{defense:.2f}")
    console.print(table)


@app.command()
def simulate(
    iterations: int = typer.Option(10_000, help="Número de simulações."),
    seed: int = typer.Option(2026, help="Seed para reprodutibilidade."),
) -> None:
    """Simula o torneio (Monte Carlo) e exibe as chances de título."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        repo.create_schema()
        config = build_default_config(repo, iterations=iterations, seed=seed)
        result = run_simulation(repo, config)

    table = Table(title=f"Chances de título ({result.iterations} simulações)")
    table.add_column("Seleção", style="bold")
    table.add_column("Classificação", justify="right")
    table.add_column("Título", justify="right")
    for team in result.teams:
        table.add_row(
            team.team_id,
            f"{team.qualified_probability:.1%}",
            f"{team.champion_probability:.1%}",
        )
    console.print(table)


@ui_app.command("serve")
def ui_serve(
    port: int = typer.Option(8501, help="Porta do Streamlit."),
) -> None:
    """Sobe o dashboard Streamlit."""
    app_path = Path("apps/streamlit/app.py")
    if not app_path.exists():
        console.print(f"[red]App não encontrado: {app_path}[/]")
        raise typer.Exit(code=1)
    subprocess.run(  # nosec B603
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(port)],
        check=True,
    )


@pool_app.command("run")
def pool_run() -> None:
    """Roda o Bolão de IAs sobre o histórico e exibe a classificação."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        repo.create_schema()
        summary = run_backtest(repo)

    table = Table(title=f"Bolão de IAs ({summary.matches_evaluated} partidas avaliadas)")
    table.add_column("Preditor", style="bold")
    table.add_column("Palpites", justify="right")
    table.add_column("Pontos", justify="right")
    table.add_column("Placar exato", justify="right")
    table.add_column("Brier médio", justify="right")
    for standing in summary.standings:
        table.add_row(
            standing.predictor_name,
            str(standing.predictions),
            str(standing.total_points),
            str(standing.exact_scores),
            f"{standing.mean_brier:.3f}",
        )
    console.print(table)


@llm_app.command("benchmark")
def llm_benchmark(
    home: str = typer.Option(..., help="team_id do mandante."),
    away: str = typer.Option(..., help="team_id do visitante."),
    question: str = typer.Option(
        "Quem tem mais chance de vencer e por quê?", help="Pergunta ao modelo."
    ),
) -> None:
    """Compara os LLMs locais (LM Studio) numa pergunta. Requer modelos carregados."""
    settings = get_settings()
    specs = list(load_model_specs().values())
    client = LMStudioClient(
        base_url=settings.lmstudio_base_url,
        api_key=settings.lmstudio_api_key,
        timeout=float(settings.lmstudio_timeout_seconds),
    )
    with DuckDBRepository(settings.duckdb_path) as repo:
        repo.create_schema()
        pack = build_evidence_pack(repo, home, away)
    rows = benchmark_models(client, specs, question, pack)

    table = Table(title="Benchmark de LLMs locais")
    table.add_column("Modelo", style="bold")
    table.add_column("Papel")
    table.add_column("Schema OK", justify="center")
    table.add_column("Grounded", justify="right")
    table.add_column("Latência (ms)", justify="right")
    table.add_column("tok/s", justify="right")
    for row in rows:
        table.add_row(
            row.model_id,
            row.role,
            "✓" if row.schema_valid else "✗",
            f"{row.grounded_ratio:.0%}",
            f"{row.latency_ms:.0f}",
            f"{row.tokens_per_second:.1f}" if row.tokens_per_second else "-",
        )
    console.print(table)


if __name__ == "__main__":
    app()
