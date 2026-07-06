"""Servidor `copamind-mcp` (MASTER_PLAN §13).

Expõe as ferramentas ao agente via MCP (stdio). O pacote `mcp` é importado de
forma preguiçosa para não ser obrigatório fora do uso do servidor. Ferramentas
read-only e de escrita são registradas separadamente; a escrita usa apenas
`add_user_report` e requer confirmação da aplicação cliente.
"""

from __future__ import annotations

from typing import Any

from copamind.core.config import get_settings
from copamind.data.repositories import DuckDBRepository
from copamind.mcp import tools


def _with_repo(func: Any, *args: Any, **kwargs: Any) -> Any:
    """Abre um repositório da configuração e executa uma ferramenta."""
    settings = get_settings()
    with DuckDBRepository(settings.duckdb_path) as repo:
        repo.create_schema()
        return func(repo, *args, **kwargs)


def create_server() -> Any:
    """Cria o servidor MCP (requer o extra `mcp`)."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - depende do extra 'mcp'
        raise RuntimeError(
            "pacote 'mcp' não instalado. Instale com: pip install -e '.[mcp]'"
        ) from exc

    server = FastMCP("copamind")

    @server.tool()
    def list_teams() -> list[dict[str, Any]]:
        """Lista as seleções cadastradas."""
        return _with_repo(tools.list_teams)

    @server.tool()
    def get_team(team_id: str) -> dict[str, Any] | None:
        """Retorna uma seleção pelo id."""
        return _with_repo(tools.get_team, team_id)

    @server.tool()
    def get_last_matches(team_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Últimas partidas finalizadas de uma seleção."""
        return _with_repo(tools.get_last_matches, team_id, limit)

    @server.tool()
    def get_head_to_head(team_a: str, team_b: str, limit: int = 10) -> list[dict[str, Any]]:
        """Confrontos diretos entre duas seleções."""
        return _with_repo(tools.get_head_to_head, team_a, team_b, limit)

    @server.tool()
    def get_team_form(team_id: str) -> dict[str, Any]:
        """Rating Elo e forma recente de uma seleção."""
        return _with_repo(tools.get_team_form, team_id)

    @server.tool()
    def predict_match(
        home_team_id: str, away_team_id: str, neutral_venue: bool = False
    ) -> dict[str, Any]:
        """Previsão 1x2 (Poisson/Dixon-Coles)."""
        return _with_repo(tools.predict_match, home_team_id, away_team_id, neutral_venue)

    @server.tool()
    def ensemble_predict(
        home_team_id: str, away_team_id: str, neutral_venue: bool = False
    ) -> dict[str, Any]:
        """Previsão 1x2 do ensemble (Elo + Poisson)."""
        return _with_repo(tools.ensemble_predict, home_team_id, away_team_id, neutral_venue)

    @server.tool()
    def run_tournament_simulation(
        iterations: int = 10_000, seed: int = 2026
    ) -> list[dict[str, Any]]:
        """Simula o torneio e retorna as probabilidades por seleção."""
        return _with_repo(tools.run_tournament_simulation, iterations, seed)

    @server.tool()
    def get_data_freshness() -> dict[str, Any]:
        """Estado e frescor da base."""
        return _with_repo(tools.get_data_freshness)

    @server.tool()
    def get_pool_leaderboard() -> list[dict[str, Any]]:
        """Classificação do Bolão de IAs."""
        return _with_repo(tools.get_pool_leaderboard)

    @server.tool()
    def search_knowledge(query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Busca RAG sobre os relatos do usuário."""
        return _with_repo(tools.search_knowledge, query, top_k)

    @server.tool()
    def add_user_report(text: str) -> dict[str, Any]:
        """(ESCRITA) Registra um relato do usuário (não verificado)."""
        return _with_repo(tools.add_user_report, text)

    return server


def main() -> None:  # pragma: no cover - ponto de entrada do servidor
    """Executa o servidor MCP em stdio."""
    create_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
