"""Repositório DuckDB — criação idempotente de tabelas e CRUD mínimo.

MASTER_PLAN §5.2 (dados estruturados em DuckDB) e §18 (anti-leakage via
``available_at``).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import duckdb

from copamind.data.schemas import (
    Match,
    MatchStatus,
    PoolPrediction,
    PoolResult,
    Prediction,
    Snapshot,
    Team,
    UserReport,
)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    description VARCHAR NOT NULL DEFAULT '',
    dataset_version VARCHAR NOT NULL DEFAULT '0.1.0'
);

CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    fifa_code VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    confederation VARCHAR,
    fifa_ranking INTEGER,
    elo_rating DOUBLE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    source VARCHAR NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    snapshot_id VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    match_id VARCHAR PRIMARY KEY,
    competition VARCHAR NOT NULL,
    stage VARCHAR NOT NULL,
    match_date TIMESTAMP NOT NULL,
    home_team_id VARCHAR NOT NULL,
    away_team_id VARCHAR NOT NULL,
    neutral_venue BOOLEAN NOT NULL DEFAULT FALSE,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR NOT NULL,
    importance_weight DOUBLE NOT NULL DEFAULT 1.0,
    source VARCHAR NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    snapshot_id VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id VARCHAR PRIMARY KEY,
    snapshot_id VARCHAR NOT NULL,
    match_id VARCHAR,
    model_name VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    home_team_id VARCHAR NOT NULL,
    away_team_id VARCHAR NOT NULL,
    home_win_probability DOUBLE NOT NULL,
    draw_probability DOUBLE NOT NULL,
    away_win_probability DOUBLE NOT NULL,
    expected_home_goals DOUBLE NOT NULL,
    expected_away_goals DOUBLE NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pool_predictions (
    prediction_id VARCHAR PRIMARY KEY,
    predictor_name VARCHAR NOT NULL,
    match_id VARCHAR NOT NULL,
    snapshot_id VARCHAR NOT NULL,
    home_team_id VARCHAR NOT NULL,
    away_team_id VARCHAR NOT NULL,
    prob_home DOUBLE NOT NULL,
    prob_draw DOUBLE NOT NULL,
    prob_away DOUBLE NOT NULL,
    predicted_home_goals INTEGER NOT NULL,
    predicted_away_goals INTEGER NOT NULL,
    locked_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pool_results (
    match_id VARCHAR PRIMARY KEY,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    recorded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS user_reports (
    report_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    is_current BOOLEAN NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    session_id VARCHAR,
    user_text VARCHAR NOT NULL,
    report_type VARCHAR NOT NULL,
    parsed_payload VARCHAR NOT NULL,
    entities VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    verified BOOLEAN NOT NULL,
    confidence DOUBLE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    snapshot_id VARCHAR NOT NULL,
    PRIMARY KEY (report_id, version)
);
"""

_TEAM_COLUMNS = (
    "team_id",
    "name",
    "fifa_code",
    "country",
    "confederation",
    "fifa_ranking",
    "elo_rating",
    "active",
    "source",
    "collected_at",
    "available_at",
    "snapshot_id",
)

_MATCH_COLUMNS = (
    "match_id",
    "competition",
    "stage",
    "match_date",
    "home_team_id",
    "away_team_id",
    "neutral_venue",
    "home_score",
    "away_score",
    "status",
    "importance_weight",
    "source",
    "collected_at",
    "available_at",
    "snapshot_id",
)

_PREDICTION_COLUMNS = (
    "prediction_id",
    "snapshot_id",
    "match_id",
    "model_name",
    "model_version",
    "home_team_id",
    "away_team_id",
    "home_win_probability",
    "draw_probability",
    "away_win_probability",
    "expected_home_goals",
    "expected_away_goals",
    "created_at",
)

_POOL_PREDICTION_COLUMNS = (
    "prediction_id",
    "predictor_name",
    "match_id",
    "snapshot_id",
    "home_team_id",
    "away_team_id",
    "prob_home",
    "prob_draw",
    "prob_away",
    "predicted_home_goals",
    "predicted_away_goals",
    "locked_at",
)

_POOL_RESULT_COLUMNS = ("match_id", "home_score", "away_score", "recorded_at")

_USER_REPORT_COLUMNS = (
    "report_id",
    "version",
    "is_current",
    "deleted",
    "session_id",
    "user_text",
    "report_type",
    "parsed_payload",
    "entities",
    "source_type",
    "verified",
    "confidence",
    "created_at",
    "available_at",
    "snapshot_id",
)


def _placeholders(n: int) -> str:
    return ", ".join(["?"] * n)


class DuckDBRepository:
    """Acesso à base DuckDB. Usável como context manager."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(self._path)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Fecha a conexão."""
        self._con.close()

    def create_schema(self) -> None:
        """Cria as tabelas de forma idempotente."""
        self._con.execute(_SCHEMA_SQL)

    # -- Snapshots -----------------------------------------------------------
    def upsert_snapshot(self, snapshot: Snapshot) -> None:
        """Insere ou substitui um snapshot."""
        self._con.execute(
            "INSERT OR REPLACE INTO snapshots "
            "(snapshot_id, created_at, description, dataset_version) VALUES (?, ?, ?, ?)",
            [
                snapshot.snapshot_id,
                snapshot.created_at,
                snapshot.description,
                snapshot.dataset_version,
            ],
        )

    # -- Teams ---------------------------------------------------------------
    def upsert_teams(self, teams: list[Team]) -> int:
        """Insere ou substitui seleções. Retorna a quantidade processada."""
        sql = (
            f"INSERT OR REPLACE INTO teams ({', '.join(_TEAM_COLUMNS)}) "
            f"VALUES ({_placeholders(len(_TEAM_COLUMNS))})"
        )
        rows = [
            [
                t.team_id,
                t.name,
                t.fifa_code,
                t.country,
                t.confederation.value if t.confederation else None,
                t.fifa_ranking,
                t.elo_rating,
                t.active,
                t.source,
                t.collected_at,
                t.available_at,
                t.snapshot_id,
            ]
            for t in teams
        ]
        self._con.executemany(sql, rows)
        return len(rows)

    def list_teams(self) -> list[Team]:
        """Lista todas as seleções ordenadas por nome."""
        cursor = self._con.execute(f"SELECT {', '.join(_TEAM_COLUMNS)} FROM teams ORDER BY name")
        return [Team(**row) for row in _rows_to_dicts(cursor)]

    def get_team(self, team_id: str) -> Team | None:
        """Retorna uma seleção pelo id ou ``None``."""
        cursor = self._con.execute(
            f"SELECT {', '.join(_TEAM_COLUMNS)} FROM teams WHERE team_id = ?",
            [team_id],
        )
        dicts = _rows_to_dicts(cursor)
        return Team(**dicts[0]) if dicts else None

    # -- Matches -------------------------------------------------------------
    def upsert_matches(self, matches: list[Match]) -> int:
        """Insere ou substitui partidas. Retorna a quantidade processada."""
        sql = (
            f"INSERT OR REPLACE INTO matches ({', '.join(_MATCH_COLUMNS)}) "
            f"VALUES ({_placeholders(len(_MATCH_COLUMNS))})"
        )
        rows = [
            [
                m.match_id,
                m.competition,
                str(m.stage),
                m.match_date,
                m.home_team_id,
                m.away_team_id,
                m.neutral_venue,
                m.home_score,
                m.away_score,
                str(m.status),
                m.importance_weight,
                m.source,
                m.collected_at,
                m.available_at,
                m.snapshot_id,
            ]
            for m in matches
        ]
        self._con.executemany(sql, rows)
        return len(rows)

    def list_matches(self, limit: int | None = None) -> list[Match]:
        """Lista partidas ordenadas por data (desc)."""
        sql = f"SELECT {', '.join(_MATCH_COLUMNS)} FROM matches ORDER BY match_date DESC"
        params: list[Any] = []
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cursor = self._con.execute(sql, params)
        return [Match(**row) for row in _rows_to_dicts(cursor)]

    def list_finished_matches(self, *, as_of: datetime | None = None) -> list[Match]:
        """Lista partidas finalizadas em ordem cronológica crescente.

        Ideal para processar ratings (Elo). Se ``as_of`` for informado,
        considera apenas dados disponíveis até esse instante (anti-leakage).
        """
        sql = f"SELECT {', '.join(_MATCH_COLUMNS)} FROM matches WHERE status = ?"
        params: list[Any] = [str(MatchStatus.finished)]
        if as_of is not None:
            sql += " AND available_at <= ?"
            params.append(as_of)
        sql += " ORDER BY match_date ASC, match_id ASC"
        cursor = self._con.execute(sql, params)
        return [Match(**row) for row in _rows_to_dicts(cursor)]

    def get_last_matches(
        self,
        team_id: str,
        limit: int = 5,
        *,
        as_of: datetime | None = None,
    ) -> list[Match]:
        """Retorna as últimas partidas finalizadas de uma seleção.

        Args:
            team_id: id da seleção.
            limit: número máximo de partidas.
            as_of: se informado, considera apenas dados disponíveis até esse
                instante (``available_at <= as_of``), prevenindo vazamento
                temporal (MASTER_PLAN §18).
        """
        sql = (
            f"SELECT {', '.join(_MATCH_COLUMNS)} FROM matches "
            "WHERE (home_team_id = ? OR away_team_id = ?) AND status = ?"
        )
        params: list[Any] = [team_id, team_id, str(MatchStatus.finished)]
        if as_of is not None:
            sql += " AND available_at <= ?"
            params.append(as_of)
        sql += " ORDER BY match_date DESC LIMIT ?"
        params.append(limit)
        cursor = self._con.execute(sql, params)
        return [Match(**row) for row in _rows_to_dicts(cursor)]

    # -- Predictions ---------------------------------------------------------
    def upsert_prediction(self, prediction: Prediction) -> None:
        """Insere ou substitui uma previsão."""
        sql = (
            f"INSERT OR REPLACE INTO predictions ({', '.join(_PREDICTION_COLUMNS)}) "
            f"VALUES ({_placeholders(len(_PREDICTION_COLUMNS))})"
        )
        self._con.execute(
            sql,
            [
                prediction.prediction_id,
                prediction.snapshot_id,
                prediction.match_id,
                prediction.model_name,
                prediction.model_version,
                prediction.home_team_id,
                prediction.away_team_id,
                prediction.home_win_probability,
                prediction.draw_probability,
                prediction.away_win_probability,
                prediction.expected_home_goals,
                prediction.expected_away_goals,
                prediction.created_at,
            ],
        )

    def list_predictions(self, limit: int | None = None) -> list[Prediction]:
        """Lista previsões ordenadas por criação (desc)."""
        sql = f"SELECT {', '.join(_PREDICTION_COLUMNS)} FROM predictions ORDER BY created_at DESC"
        params: list[Any] = []
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cursor = self._con.execute(sql, params)
        return [Prediction(**row) for row in _rows_to_dicts(cursor)]

    def latest_snapshot_id(self) -> str | None:
        """Retorna o id do snapshot mais recente, se houver."""
        result = self._con.execute(
            "SELECT snapshot_id FROM snapshots ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return str(result[0]) if result else None

    # -- Bolão de IAs (E11) --------------------------------------------------
    def insert_pool_prediction(self, prediction: PoolPrediction) -> None:
        """Insere um palpite imutável do bolão.

        Raises:
            ValueError: se já existir palpite deste preditor para a partida
                (palpites são travados e não podem ser sobrescritos).
        """
        existing = self._con.execute(
            "SELECT 1 FROM pool_predictions WHERE prediction_id = ?",
            [prediction.prediction_id],
        ).fetchone()
        if existing is not None:
            raise ValueError(f"palpite já travado: {prediction.prediction_id}")
        sql = (
            f"INSERT INTO pool_predictions ({', '.join(_POOL_PREDICTION_COLUMNS)}) "
            f"VALUES ({_placeholders(len(_POOL_PREDICTION_COLUMNS))})"
        )
        self._con.execute(
            sql,
            [
                prediction.prediction_id,
                prediction.predictor_name,
                prediction.match_id,
                prediction.snapshot_id,
                prediction.home_team_id,
                prediction.away_team_id,
                prediction.prob_home,
                prediction.prob_draw,
                prediction.prob_away,
                prediction.predicted_home_goals,
                prediction.predicted_away_goals,
                prediction.locked_at,
            ],
        )

    def pool_prediction_exists(self, prediction_id: str) -> bool:
        """Indica se um palpite específico já foi travado."""
        row = self._con.execute(
            "SELECT 1 FROM pool_predictions WHERE prediction_id = ?", [prediction_id]
        ).fetchone()
        return row is not None

    def list_pool_predictions(self) -> list[PoolPrediction]:
        """Lista todos os palpites do bolão."""
        cursor = self._con.execute(
            f"SELECT {', '.join(_POOL_PREDICTION_COLUMNS)} FROM pool_predictions"
        )
        return [PoolPrediction(**row) for row in _rows_to_dicts(cursor)]

    def upsert_pool_result(self, result: PoolResult) -> None:
        """Insere ou substitui o resultado real de uma partida do bolão."""
        sql = (
            f"INSERT OR REPLACE INTO pool_results ({', '.join(_POOL_RESULT_COLUMNS)}) "
            f"VALUES ({_placeholders(len(_POOL_RESULT_COLUMNS))})"
        )
        self._con.execute(
            sql,
            [result.match_id, result.home_score, result.away_score, result.recorded_at],
        )

    def list_pool_results(self) -> list[PoolResult]:
        """Lista os resultados registrados do bolão."""
        cursor = self._con.execute(f"SELECT {', '.join(_POOL_RESULT_COLUMNS)} FROM pool_results")
        return [PoolResult(**row) for row in _rows_to_dicts(cursor)]

    # -- User reports (E2) ---------------------------------------------------
    def insert_user_report(self, report: UserReport) -> None:
        """Insere uma versão de relato do usuário."""
        sql = (
            f"INSERT INTO user_reports ({', '.join(_USER_REPORT_COLUMNS)}) "
            f"VALUES ({_placeholders(len(_USER_REPORT_COLUMNS))})"
        )
        self._con.execute(sql, _user_report_row(report))

    def add_user_report_version(self, report: UserReport) -> None:
        """Adiciona uma nova versão como atual, desmarcando as anteriores."""
        self._con.execute(
            "UPDATE user_reports SET is_current = FALSE WHERE report_id = ?",
            [report.report_id],
        )
        self.insert_user_report(report)

    def current_user_report_version(self, report_id: str) -> int:
        """Maior número de versão existente para um relato (0 se inexistente)."""
        result = self._con.execute(
            "SELECT max(version) FROM user_reports WHERE report_id = ?", [report_id]
        ).fetchone()
        return int(result[0]) if result and result[0] is not None else 0

    def get_user_report(self, report_id: str) -> UserReport | None:
        """Retorna a versão atual e não deletada de um relato."""
        cursor = self._con.execute(
            f"SELECT {', '.join(_USER_REPORT_COLUMNS)} FROM user_reports "
            "WHERE report_id = ? AND is_current = TRUE AND deleted = FALSE",
            [report_id],
        )
        dicts = _rows_to_dicts(cursor)
        return _row_to_user_report(dicts[0]) if dicts else None

    def list_user_reports(self) -> list[UserReport]:
        """Lista os relatos atuais e não deletados."""
        cursor = self._con.execute(
            f"SELECT {', '.join(_USER_REPORT_COLUMNS)} FROM user_reports "
            "WHERE is_current = TRUE AND deleted = FALSE ORDER BY created_at DESC"
        )
        return [_row_to_user_report(row) for row in _rows_to_dicts(cursor)]

    def count(self, table: str) -> int:
        """Conta linhas de uma tabela conhecida."""
        known = {
            "teams",
            "matches",
            "snapshots",
            "predictions",
            "pool_predictions",
            "pool_results",
            "user_reports",
        }
        if table not in known:
            raise ValueError(f"tabela desconhecida: {table}")
        result = self._con.execute(f"SELECT count(*) FROM {table}").fetchone()
        return int(result[0]) if result else 0


def _rows_to_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Converte o resultado de um cursor em dicionários por nome de coluna."""
    description = cursor.description
    if description is None:
        return []
    columns = [col[0] for col in description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _user_report_row(report: UserReport) -> list[Any]:
    """Serializa um UserReport para inserção (payload/entities como JSON)."""
    return [
        report.report_id,
        report.version,
        report.is_current,
        report.deleted,
        report.session_id,
        report.user_text,
        str(report.report_type),
        json.dumps(report.parsed_payload, ensure_ascii=False),
        json.dumps(report.entities, ensure_ascii=False),
        report.source_type,
        report.verified,
        report.confidence,
        report.created_at,
        report.available_at,
        report.snapshot_id,
    ]


def _row_to_user_report(row: dict[str, Any]) -> UserReport:
    """Desserializa uma linha de user_reports em UserReport."""
    data = dict(row)
    data["parsed_payload"] = json.loads(data["parsed_payload"])
    data["entities"] = json.loads(data["entities"])
    return UserReport(**data)
