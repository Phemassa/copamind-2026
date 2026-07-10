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
    PlayerRating,
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

CREATE TABLE IF NOT EXISTS pool_prediction_payloads (
    prediction_id VARCHAR PRIMARY KEY,
    predictor_name VARCHAR NOT NULL,
    match_id VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS match_feature_snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    match_id VARCHAR NOT NULL,
    phase VARCHAR NOT NULL,
    as_of TIMESTAMP NOT NULL,
    features_json VARCHAR NOT NULL,
    baseline_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_pool_rounds (
    round_id VARCHAR PRIMARY KEY,
    match_id VARCHAR NOT NULL,
    batch_id VARCHAR,
    phase VARCHAR,
    created_at TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL,
    samples_per_model INTEGER NOT NULL,
    selected_models_json VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_phase_batches (
    batch_id VARCHAR PRIMARY KEY,
    phase VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL,
    match_count INTEGER NOT NULL,
    selected_models_json VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_model_runs (
    run_id VARCHAR PRIMARY KEY,
    round_id VARCHAR NOT NULL,
    match_id VARCHAR NOT NULL,
    model_id VARCHAR NOT NULL,
    predictor_name VARCHAR NOT NULL,
    sample_index INTEGER NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms DOUBLE NOT NULL,
    raw_response VARCHAR,
    valid BOOLEAN NOT NULL,
    error VARCHAR,
    attempts_json VARCHAR NOT NULL,
    pick_json VARCHAR,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_model_consensus (
    consensus_id VARCHAR PRIMARY KEY,
    round_id VARCHAR NOT NULL,
    match_id VARCHAR NOT NULL,
    model_id VARCHAR NOT NULL,
    predictor_name VARCHAR NOT NULL,
    valid_samples INTEGER NOT NULL,
    total_samples INTEGER NOT NULL,
    prob_home DOUBLE NOT NULL,
    prob_draw DOUBLE NOT NULL,
    prob_away DOUBLE NOT NULL,
    predicted_home_goals INTEGER NOT NULL,
    predicted_away_goals INTEGER NOT NULL,
    winner VARCHAR NOT NULL,
    first_goal_scorer VARCHAR,
    coherence_score DOUBLE NOT NULL,
    coherence_notes VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS player_ratings (
    player_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    team_id VARCHAR NOT NULL,
    position VARCHAR NOT NULL,
    age INTEGER NOT NULL,
    overall INTEGER NOT NULL,
    pace INTEGER NOT NULL,
    shooting INTEGER NOT NULL,
    passing INTEGER NOT NULL,
    dribbling INTEGER NOT NULL,
    defending INTEGER NOT NULL,
    physical INTEGER NOT NULL,
    copa_goals INTEGER NOT NULL DEFAULT 0,
    copa_assists INTEGER NOT NULL DEFAULT 0,
    copa_matches INTEGER NOT NULL DEFAULT 0,
    source VARCHAR NOT NULL,
    snapshot_id VARCHAR NOT NULL
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

CREATE TABLE IF NOT EXISTS team_context_notes (
    note_id VARCHAR PRIMARY KEY,
    phase VARCHAR NOT NULL,
    team_id VARCHAR NOT NULL,
    match_id VARCHAR,
    note_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    note_text VARCHAR NOT NULL,
    impact_json VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    source_url VARCHAR,
    confidence DOUBLE NOT NULL,
    weight DOUBLE NOT NULL,
    available_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    memory_summary VARCHAR NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    batch_id VARCHAR,
    role VARCHAR NOT NULL,
    model_id VARCHAR,
    content VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    latency_ms DOUBLE,
    metadata_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_batches (
    batch_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    question_message_id VARCHAR NOT NULL,
    selected_models_json VARCHAR NOT NULL,
    use_memory BOOLEAN NOT NULL,
    status VARCHAR NOT NULL,
    current_model_id VARCHAR,
    completed_models INTEGER NOT NULL DEFAULT 0,
    error VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_news (
    news_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    summary VARCHAR NOT NULL,
    published_at VARCHAR,
    entities_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
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
        self._closed = False
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
        if self._closed:
            return
        self._con.close()
        self._closed = True

    def create_schema(self) -> None:
        """Cria as tabelas de forma idempotente."""
        self._con.execute(_SCHEMA_SQL)
        self._ensure_schema_migrations()

    @property
    def path(self) -> str:
        """Caminho usado pela conexao (util para workers com conexao propria)."""
        return self._path

    def _ensure_schema_migrations(self) -> None:
        """Aplica pequenas migracoes idempotentes em bancos existentes."""
        self._add_column_if_missing("llm_pool_rounds", "batch_id", "VARCHAR")
        self._add_column_if_missing("llm_pool_rounds", "phase", "VARCHAR")

    def _add_column_if_missing(self, table: str, column: str, column_type: str) -> None:
        columns = {
            str(row[1])
            for row in self._con.execute(f"PRAGMA table_info('{table}')").fetchall()
        }
        if column not in columns:
            self._con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

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

    def upsert_pool_prediction_payload(
        self,
        prediction_id: str,
        predictor_name: str,
        match_id: str,
        payload: dict[str, Any],
        created_at: datetime,
    ) -> None:
        """Guarda o payload completo de um palpite de LLM."""
        self._con.execute(
            "INSERT OR REPLACE INTO pool_prediction_payloads "
            "(prediction_id, predictor_name, match_id, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                prediction_id,
                predictor_name,
                match_id,
                json.dumps(payload, ensure_ascii=False),
                created_at,
            ],
        )

    def list_pool_prediction_payloads(self) -> list[dict[str, Any]]:
        """Lista payloads completos de palpites de LLM."""
        cursor = self._con.execute(
            "SELECT prediction_id, predictor_name, match_id, payload_json, created_at "
            "FROM pool_prediction_payloads ORDER BY created_at DESC"
        )
        rows = _rows_to_dicts(cursor)
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    # -- Feature snapshots para ML/RAG -------------------------------------
    def upsert_match_feature_snapshot(
        self,
        *,
        snapshot_id: str,
        match_id: str,
        phase: str,
        as_of: datetime,
        features: dict[str, Any],
        baseline: dict[str, Any],
        created_at: datetime,
    ) -> None:
        """Grava o contexto estatistico usado por ML/RAG para uma partida."""
        self._con.execute(
            "INSERT OR REPLACE INTO match_feature_snapshots "
            "(snapshot_id, match_id, phase, as_of, features_json, baseline_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                snapshot_id,
                match_id,
                phase,
                as_of,
                json.dumps(features, ensure_ascii=False),
                json.dumps(baseline, ensure_ascii=False),
                created_at,
            ],
        )

    def list_match_feature_snapshots(
        self,
        *,
        phase: str | None = None,
        match_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista snapshots de features para auditoria e export."""
        sql = (
            "SELECT snapshot_id, match_id, phase, as_of, features_json, baseline_json, created_at "
            "FROM match_feature_snapshots"
        )
        params: list[Any] = []
        filters: list[str] = []
        if phase:
            filters.append("phase = ?")
            params.append(phase)
        if match_id:
            filters.append("match_id = ?")
            params.append(match_id)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY as_of ASC, match_id ASC, created_at DESC"
        rows = _rows_to_dicts(self._con.execute(sql, params))
        for row in rows:
            row["features"] = json.loads(row.pop("features_json"))
            row["baseline"] = json.loads(row.pop("baseline_json"))
        return rows

    # -- Notas contextuais controladas para LLM ----------------------------
    def upsert_team_context_note(
        self,
        *,
        note_id: str,
        phase: str,
        team_id: str,
        match_id: str | None,
        note_type: str,
        title: str,
        note_text: str,
        impact: dict[str, Any],
        source: str,
        source_url: str | None,
        confidence: float,
        weight: float,
        available_at: datetime,
        created_at: datetime,
        active: bool = True,
    ) -> None:
        """Grava uma nota manual que entra no contexto da LLM como evidencia."""
        self._con.execute(
            "INSERT OR REPLACE INTO team_context_notes "
            "(note_id, phase, team_id, match_id, note_type, title, note_text, impact_json, "
            "source, source_url, confidence, weight, available_at, created_at, active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                note_id,
                phase,
                team_id,
                match_id,
                note_type,
                title,
                note_text,
                json.dumps(impact, ensure_ascii=False),
                source,
                source_url,
                confidence,
                weight,
                available_at,
                created_at,
                active,
            ],
        )

    def list_team_context_notes(
        self,
        *,
        phase: str | None = None,
        team_id: str | None = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Lista notas contextuais manuais para portal e auditoria."""
        sql = (
            "SELECT note_id, phase, team_id, match_id, note_type, title, note_text, "
            "impact_json, source, source_url, confidence, weight, available_at, created_at, active "
            "FROM team_context_notes"
        )
        params: list[Any] = []
        filters: list[str] = []
        if phase:
            filters.append("phase = ?")
            params.append(phase)
        if team_id:
            filters.append("team_id = ?")
            params.append(team_id)
        if active_only:
            filters.append("active = TRUE")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY available_at DESC, created_at DESC"
        rows = _rows_to_dicts(self._con.execute(sql, params))
        for row in rows:
            row["impact"] = json.loads(row.pop("impact_json"))
        return rows

    def list_context_notes_for_match(self, match: Match) -> list[dict[str, Any]]:
        """Notas aplicaveis a uma partida, respeitando anti-vazamento."""
        sql = (
            "SELECT note_id, phase, team_id, match_id, note_type, title, note_text, "
            "impact_json, source, source_url, confidence, weight, available_at, created_at, active "
            "FROM team_context_notes "
            "WHERE active = TRUE "
            "AND phase = ? "
            "AND team_id IN (?, ?) "
            "AND (match_id IS NULL OR match_id = ?) "
            "AND available_at <= ? "
            "ORDER BY weight DESC, confidence DESC, available_at DESC"
        )
        rows = _rows_to_dicts(
            self._con.execute(
                sql,
                [
                    str(match.stage),
                    match.home_team_id,
                    match.away_team_id,
                    match.match_id,
                    match.match_date,
                ],
            )
        )
        for row in rows:
            row["impact"] = json.loads(row.pop("impact_json"))
        return rows

    def deactivate_team_context_note(self, note_id: str) -> bool:
        """Desativa uma nota sem apagar historico."""
        exists = self._count_where("team_context_notes", " WHERE note_id = ?", [note_id])
        if not exists:
            return False
        self._con.execute("UPDATE team_context_notes SET active = FALSE WHERE note_id = ?", [note_id])
        return True

    # -- Rodadas versionadas de LLM -----------------------------------------
    def insert_llm_pool_round(
        self,
        round_id: str,
        match_id: str,
        created_at: datetime,
        status: str,
        samples_per_model: int,
        selected_models: list[str],
        *,
        batch_id: str | None = None,
        phase: str | None = None,
    ) -> None:
        """Cria uma rodada versionada do bolão das LLMs."""
        self._con.execute(
            "INSERT INTO llm_pool_rounds "
            "(round_id, match_id, batch_id, phase, created_at, status, "
            "samples_per_model, selected_models_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                round_id,
                match_id,
                batch_id,
                phase,
                created_at,
                status,
                samples_per_model,
                json.dumps(selected_models, ensure_ascii=False),
            ],
        )

    def update_llm_pool_round_status(self, round_id: str, status: str) -> None:
        """Atualiza o status de uma rodada."""
        self._con.execute(
            "UPDATE llm_pool_rounds SET status = ? WHERE round_id = ?",
            [status, round_id],
        )

    def insert_llm_phase_batch(
        self,
        batch_id: str,
        phase: str,
        created_at: datetime,
        status: str,
        match_count: int,
        selected_models: list[str],
    ) -> None:
        """Cria um batch de rodadas LLM para uma fase."""
        self._con.execute(
            "INSERT INTO llm_phase_batches "
            "(batch_id, phase, created_at, status, match_count, selected_models_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                batch_id,
                phase,
                created_at,
                status,
                match_count,
                json.dumps(selected_models, ensure_ascii=False),
            ],
        )

    def update_llm_phase_batch_status(self, batch_id: str, status: str) -> None:
        """Atualiza o status de um batch de fase."""
        self._con.execute(
            "UPDATE llm_phase_batches SET status = ? WHERE batch_id = ?",
            [status, batch_id],
        )

    def insert_llm_model_run(
        self,
        *,
        run_id: str,
        round_id: str,
        match_id: str,
        model_id: str,
        predictor_name: str,
        sample_index: int,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        latency_ms: float,
        raw_response: str | None,
        valid: bool,
        error: str | None,
        attempts: list[dict[str, object]],
        pick: dict[str, Any] | None,
        created_at: datetime,
    ) -> None:
        """Registra uma chamada individual de modelo."""
        self._con.execute(
            "INSERT INTO llm_model_runs "
            "(run_id, round_id, match_id, model_id, predictor_name, sample_index, "
            "prompt_tokens, completion_tokens, latency_ms, raw_response, valid, error, "
            "attempts_json, pick_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                run_id,
                round_id,
                match_id,
                model_id,
                predictor_name,
                sample_index,
                prompt_tokens,
                completion_tokens,
                latency_ms,
                raw_response,
                valid,
                error,
                json.dumps(attempts, ensure_ascii=False),
                json.dumps(pick, ensure_ascii=False) if pick is not None else None,
                created_at,
            ],
        )

    def upsert_llm_model_consensus(
        self,
        *,
        consensus_id: str,
        round_id: str,
        match_id: str,
        model_id: str,
        predictor_name: str,
        valid_samples: int,
        total_samples: int,
        prob_home: float,
        prob_draw: float,
        prob_away: float,
        predicted_home_goals: int,
        predicted_away_goals: int,
        winner: str,
        first_goal_scorer: str | None,
        coherence_score: float,
        coherence_notes: str,
        payload: dict[str, Any],
        created_at: datetime,
    ) -> None:
        """Grava a palavra final de um modelo em uma rodada."""
        self._con.execute(
            "INSERT OR REPLACE INTO llm_model_consensus "
            "(consensus_id, round_id, match_id, model_id, predictor_name, valid_samples, "
            "total_samples, prob_home, prob_draw, prob_away, predicted_home_goals, "
            "predicted_away_goals, winner, first_goal_scorer, coherence_score, "
            "coherence_notes, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                consensus_id,
                round_id,
                match_id,
                model_id,
                predictor_name,
                valid_samples,
                total_samples,
                prob_home,
                prob_draw,
                prob_away,
                predicted_home_goals,
                predicted_away_goals,
                winner,
                first_goal_scorer,
                coherence_score,
                coherence_notes,
                json.dumps(payload, ensure_ascii=False),
                created_at,
            ],
        )

    def list_llm_pool_rounds(
        self,
        match_id: str | None = None,
        *,
        batch_id: str | None = None,
        phase: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista rodadas do bolão das LLMs."""
        sql = (
            "SELECT round_id, match_id, batch_id, phase, created_at, status, samples_per_model, "
            "selected_models_json FROM llm_pool_rounds"
        )
        params: list[Any] = []
        filters: list[str] = []
        if match_id:
            filters.append("match_id = ?")
            params.append(match_id)
        if batch_id:
            filters.append("batch_id = ?")
            params.append(batch_id)
        if phase:
            filters.append("phase = ?")
            params.append(phase)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY created_at DESC"
        rows = _rows_to_dicts(self._con.execute(sql, params))
        for row in rows:
            row["selected_models"] = json.loads(row.pop("selected_models_json"))
        return rows

    def list_llm_phase_batches(self, phase: str | None = None) -> list[dict[str, Any]]:
        """Lista batches de execucao por fase."""
        sql = (
            "SELECT batch_id, phase, created_at, status, match_count, selected_models_json "
            "FROM llm_phase_batches"
        )
        params: list[Any] = []
        if phase:
            sql += " WHERE phase = ?"
            params.append(phase)
        sql += " ORDER BY created_at DESC"
        rows = _rows_to_dicts(self._con.execute(sql, params))
        for row in rows:
            row["selected_models"] = json.loads(row.pop("selected_models_json"))
        return rows

    def list_llm_model_runs(self, round_id: str | None = None) -> list[dict[str, Any]]:
        """Lista chamadas individuais de LLM."""
        sql = (
            "SELECT run_id, round_id, match_id, model_id, predictor_name, sample_index, "
            "prompt_tokens, completion_tokens, latency_ms, raw_response, valid, error, "
            "attempts_json, pick_json, created_at FROM llm_model_runs"
        )
        params: list[Any] = []
        if round_id:
            sql += " WHERE round_id = ?"
            params.append(round_id)
        sql += " ORDER BY created_at DESC, sample_index ASC"
        rows = _rows_to_dicts(self._con.execute(sql, params))
        for row in rows:
            row["attempts"] = json.loads(row.pop("attempts_json"))
            pick_json = row.pop("pick_json")
            row["pick"] = json.loads(pick_json) if pick_json else None
        return rows

    def list_llm_model_consensus(self, round_id: str | None = None) -> list[dict[str, Any]]:
        """Lista consensos/palavras finais de LLM."""
        sql = (
            "SELECT consensus_id, round_id, match_id, model_id, predictor_name, "
            "valid_samples, total_samples, prob_home, prob_draw, prob_away, "
            "predicted_home_goals, predicted_away_goals, winner, first_goal_scorer, "
            "coherence_score, coherence_notes, payload_json, created_at "
            "FROM llm_model_consensus"
        )
        params: list[Any] = []
        if round_id:
            sql += " WHERE round_id = ?"
            params.append(round_id)
        sql += " ORDER BY created_at DESC"
        rows = _rows_to_dicts(self._con.execute(sql, params))
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def llm_model_metrics(self) -> list[dict[str, Any]]:
        """Agrega telemetria historica por modelo."""
        cursor = self._con.execute(
            """
            SELECT
                r.model_id,
                count(DISTINCT r.round_id) AS total_rounds,
                count(*) AS total_runs,
                sum(CASE WHEN r.valid THEN 1 ELSE 0 END) AS valid_runs,
                avg(r.latency_ms) AS avg_latency_ms,
                avg(r.prompt_tokens) AS avg_prompt_tokens,
                avg(r.completion_tokens) AS avg_completion_tokens,
                avg(
                    CASE
                        WHEN r.completion_tokens IS NOT NULL AND r.latency_ms > 0
                        THEN r.completion_tokens / (r.latency_ms / 1000.0)
                        ELSE NULL
                    END
                ) AS avg_tokens_per_second,
                avg(c.coherence_score) AS avg_coherence_score
            FROM llm_model_runs r
            LEFT JOIN llm_model_consensus c
              ON c.round_id = r.round_id AND c.model_id = r.model_id
            GROUP BY r.model_id
            ORDER BY total_rounds DESC, valid_runs DESC, r.model_id ASC
            """
        )
        return _rows_to_dicts(cursor)

    def reset_llm_history(
        self,
        *,
        phase: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, int]:
        """Remove historico das LLMs sem apagar jogos, resultados ou dados FIFA."""
        round_ids = self._round_ids_for_reset(phase=phase)
        predictor_names = self._predictor_names_for_reset(round_ids=round_ids, model_id=model_id)
        counts = {
            "pool_predictions": self._delete_by_values(
                "pool_predictions",
                "predictor_name",
                predictor_names,
            ),
            "pool_prediction_payloads": self._delete_by_values(
                "pool_prediction_payloads",
                "predictor_name",
                predictor_names,
            ),
            "llm_model_consensus": self._delete_llm_round_table(
                "llm_model_consensus",
                round_ids=round_ids,
                model_id=model_id,
                phase=phase,
            ),
            "llm_model_runs": self._delete_llm_round_table(
                "llm_model_runs",
                round_ids=round_ids,
                model_id=model_id,
                phase=phase,
            ),
        }
        counts["pool_predictions"] += self._delete_llm_pool_table_by_scope(
            "pool_predictions",
            phase=phase,
            model_id=model_id,
        )
        counts["pool_prediction_payloads"] += self._delete_llm_pool_table_by_scope(
            "pool_prediction_payloads",
            phase=phase,
            model_id=model_id,
        )
        counts["llm_pool_rounds"] = self._delete_empty_or_selected_rounds(
            round_ids=round_ids,
            delete_all_for_scope=model_id is None,
        )
        counts["llm_phase_batches"] = self._delete_empty_or_selected_batches(
            phase=phase,
            delete_all_for_scope=model_id is None,
        )
        return counts

    def _round_ids_for_reset(self, *, phase: str | None) -> list[str]:
        sql = "SELECT round_id FROM llm_pool_rounds"
        params: list[Any] = []
        if phase:
            sql += " WHERE phase = ?"
            params.append(phase)
        return [str(row[0]) for row in self._con.execute(sql, params).fetchall()]

    def _predictor_names_for_reset(
        self,
        *,
        round_ids: list[str],
        model_id: str | None,
    ) -> list[str]:
        filters = ["predictor_name LIKE 'llm:%' OR predictor_name LIKE 'combo:%'"]
        params: list[Any] = []
        if round_ids:
            filters.append(f"round_id IN ({_placeholders(len(round_ids))})")
            params.extend(round_ids)
        if model_id:
            filters.append("model_id = ?")
            params.append(model_id)
        where = " AND ".join(f"({item})" for item in filters)
        sql = f"SELECT DISTINCT predictor_name FROM llm_model_runs WHERE {where}"
        names = [str(row[0]) for row in self._con.execute(sql, params).fetchall()]
        if model_id and round_ids:
            names.extend(f"llm:{model_id}:round:{round_id}" for round_id in round_ids)
        if round_ids:
            names.extend(f"combo:llm_pool:round:{round_id}" for round_id in round_ids)
        if not round_ids:
            names.extend(
                str(row[0])
                for row in self._con.execute(
                    "SELECT DISTINCT predictor_name FROM pool_predictions "
                    "WHERE predictor_name LIKE 'llm:%' OR predictor_name LIKE 'combo:%'"
                ).fetchall()
            )
        return sorted(set(names))

    def _delete_llm_round_table(
        self,
        table: str,
        *,
        round_ids: list[str],
        model_id: str | None,
        phase: str | None,
    ) -> int:
        if phase and not round_ids:
            return 0
        filters: list[str] = []
        params: list[Any] = []
        if round_ids:
            filters.append(f"round_id IN ({_placeholders(len(round_ids))})")
            params.extend(round_ids)
        if model_id:
            filters.append("model_id = ?")
            params.append(model_id)
        where = f" WHERE {' AND '.join(filters)}" if filters else ""
        count = self._count_where(table, where, params)
        self._con.execute(f"DELETE FROM {table}{where}", params)
        return count

    def _delete_llm_pool_table_by_scope(
        self,
        table: str,
        *,
        phase: str | None,
        model_id: str | None,
    ) -> int:
        filters: list[str] = []
        params: list[Any] = []
        predictor_filters: list[str] = []
        if model_id:
            predictor_filters.append("predictor_name LIKE ?")
            params.append(f"llm:{model_id}:round:%")
            if phase:
                predictor_filters.append("predictor_name LIKE 'combo:%'")
        else:
            predictor_filters.extend(
                ["predictor_name LIKE 'llm:%'", "predictor_name LIKE 'combo:%'"]
            )
        filters.append(f"({' OR '.join(predictor_filters)})")
        if phase:
            filters.append("match_id IN (SELECT match_id FROM matches WHERE stage = ?)")
            params.append(phase)
        where = f" WHERE {' AND '.join(filters)}"
        count = self._count_where(table, where, params)
        self._con.execute(f"DELETE FROM {table}{where}", params)
        return count

    def _delete_empty_or_selected_rounds(
        self,
        *,
        round_ids: list[str],
        delete_all_for_scope: bool,
    ) -> int:
        if delete_all_for_scope:
            return self._delete_by_values("llm_pool_rounds", "round_id", round_ids)
        empty_ids = [
            str(row[0])
            for row in self._con.execute(
                "SELECT r.round_id FROM llm_pool_rounds r "
                "LEFT JOIN llm_model_runs m ON m.round_id = r.round_id "
                "WHERE m.round_id IS NULL"
            ).fetchall()
        ]
        return self._delete_by_values("llm_pool_rounds", "round_id", empty_ids)

    def _delete_empty_or_selected_batches(
        self,
        *,
        phase: str | None,
        delete_all_for_scope: bool,
    ) -> int:
        if delete_all_for_scope:
            sql = "SELECT batch_id FROM llm_phase_batches"
            params: list[Any] = []
            if phase:
                sql += " WHERE phase = ?"
                params.append(phase)
            ids = [str(row[0]) for row in self._con.execute(sql, params).fetchall()]
            return self._delete_by_values("llm_phase_batches", "batch_id", ids)
        empty_ids = [
            str(row[0])
            for row in self._con.execute(
                "SELECT b.batch_id FROM llm_phase_batches b "
                "LEFT JOIN llm_pool_rounds r ON r.batch_id = b.batch_id "
                "WHERE r.batch_id IS NULL"
            ).fetchall()
        ]
        return self._delete_by_values("llm_phase_batches", "batch_id", empty_ids)

    def _delete_by_values(self, table: str, column: str, values: list[str]) -> int:
        if not values:
            return 0
        where = f" WHERE {column} IN ({_placeholders(len(values))})"
        count = self._count_where(table, where, list(values))
        self._con.execute(f"DELETE FROM {table}{where}", list(values))
        return count

    def _count_where(self, table: str, where: str, params: list[Any]) -> int:
        result = self._con.execute(f"SELECT count(*) FROM {table}{where}", params).fetchone()
        return int(result[0]) if result else 0

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

    # -- Player ratings ------------------------------------------------------
    def upsert_players(self, players: list[PlayerRating]) -> int:
        """Insere ou substitui ratings de jogadores. Retorna a quantidade."""
        cols = (
            "player_id", "name", "team_id", "position", "age",
            "overall", "pace", "shooting", "passing", "dribbling",
            "defending", "physical", "copa_goals", "copa_assists",
            "copa_matches", "source", "snapshot_id",
        )
        sql = (
            f"INSERT OR REPLACE INTO player_ratings ({', '.join(cols)}) "
            f"VALUES ({_placeholders(len(cols))})"
        )
        rows = [
            [p.player_id, p.name, p.team_id, p.position, p.age,
             p.overall, p.pace, p.shooting, p.passing, p.dribbling,
             p.defending, p.physical, p.copa_goals, p.copa_assists,
             p.copa_matches, p.source, p.snapshot_id]
            for p in players
        ]
        self._con.executemany(sql, rows)
        return len(rows)

    def list_players(
        self,
        team_id: str | None = None,
        position: str | None = None,
        limit: int = 200,
    ) -> list[PlayerRating]:
        """Lista jogadores com filtros opcionais."""
        sql = "SELECT * FROM player_ratings WHERE 1=1"
        params: list[object] = []
        if team_id:
            sql += " AND team_id = ?"
            params.append(team_id)
        if position:
            sql += " AND position = ?"
            params.append(position)
        sql += " ORDER BY overall DESC LIMIT ?"
        params.append(limit)
        cursor = self._con.execute(sql, params)
        return [PlayerRating(**row) for row in _rows_to_dicts(cursor)]

    def top_scorers(self, limit: int = 20) -> list[PlayerRating]:
        """Top artilheiros da Copa."""
        cursor = self._con.execute(
            "SELECT * FROM player_ratings ORDER BY copa_goals DESC, copa_assists DESC LIMIT ?",
            [limit],
        )
        return [PlayerRating(**row) for row in _rows_to_dicts(cursor)]

    # -- Chat persistente ----------------------------------------------------
    def create_chat_session(self, session_id: str, created_at: datetime) -> None:
        self._con.execute(
            "INSERT INTO chat_sessions (session_id, created_at, updated_at, memory_summary) "
            "VALUES (?, ?, ?, '')",
            [session_id, created_at, created_at],
        )

    def get_chat_session(self, session_id: str) -> dict[str, Any] | None:
        cursor = self._con.execute(
            "SELECT session_id, created_at, updated_at, memory_summary FROM chat_sessions "
            "WHERE session_id = ?",
            [session_id],
        )
        rows = _rows_to_dicts(cursor)
        return rows[0] if rows else None

    def update_chat_memory(self, session_id: str, summary: str, updated_at: datetime) -> None:
        self._con.execute(
            "UPDATE chat_sessions SET memory_summary = ?, updated_at = ? WHERE session_id = ?",
            [summary, updated_at, session_id],
        )

    def insert_chat_message(
        self,
        *,
        message_id: str,
        session_id: str,
        batch_id: str | None,
        role: str,
        content: str,
        status: str,
        created_at: datetime,
        model_id: str | None = None,
        latency_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._con.execute(
            "INSERT INTO chat_messages (message_id, session_id, batch_id, role, model_id, "
            "content, status, latency_ms, metadata_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [message_id, session_id, batch_id, role, model_id, content, status, latency_ms,
             json.dumps(metadata or {}, ensure_ascii=False), created_at],
        )

    def list_chat_messages(self, session_id: str) -> list[dict[str, Any]]:
        rows = _rows_to_dicts(self._con.execute(
            "SELECT message_id, session_id, batch_id, role, model_id, content, status, "
            "latency_ms, metadata_json, created_at FROM chat_messages "
            "WHERE session_id = ? ORDER BY created_at, message_id", [session_id]
        ))
        for row in rows:
            row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        return rows

    def insert_chat_batch(
        self, batch_id: str, session_id: str, question_message_id: str,
        selected_models: list[str], use_memory: bool, created_at: datetime,
    ) -> None:
        self._con.execute(
            "INSERT INTO chat_batches (batch_id, session_id, question_message_id, "
            "selected_models_json, use_memory, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
            [batch_id, session_id, question_message_id,
             json.dumps(selected_models, ensure_ascii=False), use_memory, created_at, created_at],
        )

    def update_chat_batch(self, batch_id: str, *, status: str, updated_at: datetime,
                          current_model_id: str | None = None, completed_models: int = 0,
                          error: str | None = None) -> None:
        self._con.execute(
            "UPDATE chat_batches SET status = ?, current_model_id = ?, completed_models = ?, "
            "error = ?, updated_at = ? WHERE batch_id = ?",
            [status, current_model_id, completed_models, error, updated_at, batch_id],
        )

    def get_chat_batch(self, batch_id: str) -> dict[str, Any] | None:
        rows = _rows_to_dicts(self._con.execute(
            "SELECT batch_id, session_id, question_message_id, selected_models_json, use_memory, "
            "status, current_model_id, completed_models, error, created_at, updated_at "
            "FROM chat_batches WHERE batch_id = ?", [batch_id]
        ))
        if not rows:
            return None
        rows[0]["selected_models"] = json.loads(rows[0].pop("selected_models_json"))
        return rows[0]

    def latest_chat_batch(self, session_id: str) -> dict[str, Any] | None:
        row = self._con.execute(
            "SELECT batch_id FROM chat_batches WHERE session_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            [session_id],
        ).fetchone()
        return self.get_chat_batch(str(row[0])) if row else None

    def insert_chat_news(self, *, news_id: str, session_id: str, source_url: str,
                         source: str, title: str, summary: str, published_at: str | None,
                         entities: list[str], created_at: datetime) -> None:
        self._con.execute(
            "INSERT INTO chat_news (news_id, session_id, source_url, source, title, summary, "
            "published_at, entities_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [news_id, session_id, source_url, source, title, summary, published_at,
             json.dumps(entities, ensure_ascii=False), created_at],
        )

    def list_chat_news(self, session_id: str) -> list[dict[str, Any]]:
        rows = _rows_to_dicts(self._con.execute(
            "SELECT news_id, session_id, source_url, source, title, summary, published_at, "
            "entities_json, created_at FROM chat_news WHERE session_id = ? ORDER BY created_at",
            [session_id],
        ))
        for row in rows:
            row["entities"] = json.loads(row.pop("entities_json") or "[]")
        return rows

    def update_chat_news(self, news_id: str, session_id: str, title: str, summary: str) -> None:
        self._con.execute(
            "UPDATE chat_news SET title = ?, summary = ? WHERE news_id = ? AND session_id = ?",
            [title, summary, news_id, session_id],
        )

    def delete_chat_session(self, session_id: str) -> int:
        exists_row = self._con.execute(
            "SELECT count(*) FROM chat_sessions WHERE session_id = ?", [session_id]
        ).fetchone()
        exists = int(exists_row[0]) if exists_row else 0
        for table in ("chat_messages", "chat_batches", "chat_news"):
            self._con.execute(f"DELETE FROM {table} WHERE session_id = ?", [session_id])
        self._con.execute("DELETE FROM chat_sessions WHERE session_id = ?", [session_id])
        return exists

    def count(self, table: str) -> int:
        """Conta linhas de uma tabela conhecida."""
        known = {
            "teams", "matches", "snapshots", "predictions",
            "pool_predictions", "pool_results", "pool_prediction_payloads",
            "match_feature_snapshots",
            "llm_pool_rounds", "llm_phase_batches", "llm_model_runs", "llm_model_consensus",
            "user_reports", "player_ratings",
            "chat_sessions", "chat_messages", "chat_batches", "chat_news",
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
