"""Testes da extração de relatos do usuário."""

from __future__ import annotations

from copamind.data.schemas import ReportType
from copamind.reports.extractors import RuleBasedExtractor


def test_extract_match_result() -> None:
    extractor = RuleBasedExtractor()
    result = extractor.extract("O Brasil venceu o México por 2 a 1 ontem.")
    assert result.report_type is ReportType.match_result
    assert result.parsed_payload["home_team"] == "O Brasil"
    assert result.parsed_payload["away_team"] == "México"
    assert result.parsed_payload["home_score"] == 2
    assert result.parsed_payload["away_score"] == 1
    assert result.confidence > 0.5


def test_extract_draw() -> None:
    extractor = RuleBasedExtractor()
    result = extractor.extract("Argentina empatou com Uruguai por 1 a 1.")
    assert result.report_type is ReportType.match_result
    assert result.parsed_payload["home_score"] == 1
    assert result.parsed_payload["away_score"] == 1


def test_extract_injury() -> None:
    extractor = RuleBasedExtractor()
    result = extractor.extract("O atacante sofreu uma lesão no treino.")
    assert result.report_type is ReportType.injury


def test_extract_general() -> None:
    extractor = RuleBasedExtractor()
    result = extractor.extract("Achei o time muito bem organizado.")
    assert result.report_type is ReportType.general
    assert result.confidence < 0.5
