"""Testes da geração de cards de conteúdo."""

from __future__ import annotations

from copamind.content.cards import championship_card, matchup_card
from copamind.data.repositories import DuckDBRepository


def test_championship_card_bilingual(seeded_repo: DuckDBRepository) -> None:
    cards = championship_card(seeded_repo, iterations=500)
    assert set(cards) == {"pt-BR", "en"}
    assert "Chances de título" in cards["pt-BR"]
    assert "Title chances" in cards["en"]
    # contém ao menos uma seleção do dataset
    assert "Nortlândia" in cards["pt-BR"]


def test_matchup_card_bilingual(seeded_repo: DuckDBRepository) -> None:
    cards = matchup_card(seeded_repo, "T-NTL", "T-SDR")
    assert set(cards) == {"pt-BR", "en"}
    assert "Nortlândia" in cards["pt-BR"]
    assert "%" in cards["pt-BR"]
    # disclaimer presente
    assert ">" in cards["en"]
