"""Validação tabular com Pandera (MASTER_PLAN §10, §27).

A validação de linha é feita pelos schemas Pydantic; aqui adicionamos uma
checagem tabular leve para DataFrames de partidas, útil em ingestão em lote.
"""

from __future__ import annotations

import pandera.polars as pa
import polars as pl
from pandera.errors import SchemaError

_MATCH_FRAME_SCHEMA = pa.DataFrameSchema(
    {
        "match_id": pa.Column(str, nullable=False),
        "home_team_id": pa.Column(str, nullable=False),
        "away_team_id": pa.Column(str, nullable=False),
        "home_score": pa.Column(int, nullable=True, checks=pa.Check.ge(0)),
        "away_score": pa.Column(int, nullable=True, checks=pa.Check.ge(0)),
    },
)


def validate_matches_frame(frame: pl.DataFrame) -> pl.DataFrame:
    """Valida um DataFrame de partidas.

    Raises:
        SchemaError: quando o DataFrame viola o schema.
    """
    validated: pl.DataFrame = _MATCH_FRAME_SCHEMA.validate(frame)
    return validated


__all__ = ["SchemaError", "validate_matches_frame"]
