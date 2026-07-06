"""Conectores de fontes externas (OpenFootball worldcup.json, etc.)."""

from copamind.data.connectors.openfootball import (
    parse_worldcup_json,
    read_worldcup_file,
)

__all__ = ["parse_worldcup_json", "read_worldcup_file"]
