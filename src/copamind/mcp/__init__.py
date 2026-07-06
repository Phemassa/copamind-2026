"""Servidor MCP do CopaMind (E6, MASTER_PLAN §13)."""

from copamind.mcp.tools import (
    READ_ONLY_TOOLS,
    WRITE_TOOLS,
    add_user_report,
    ensemble_predict,
    get_calibration,
    get_data_freshness,
    get_head_to_head,
    get_last_matches,
    get_pool_leaderboard,
    get_team,
    get_team_form,
    list_teams,
    predict_match,
    run_tournament_simulation,
    search_knowledge,
)

__all__ = [
    "READ_ONLY_TOOLS",
    "WRITE_TOOLS",
    "add_user_report",
    "ensemble_predict",
    "get_calibration",
    "get_data_freshness",
    "get_head_to_head",
    "get_last_matches",
    "get_pool_leaderboard",
    "get_team",
    "get_team_form",
    "list_teams",
    "predict_match",
    "run_tournament_simulation",
    "search_knowledge",
]
