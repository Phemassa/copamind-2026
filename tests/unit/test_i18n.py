"""Testes da internacionalização da UI."""

from __future__ import annotations

from copamind.ui.i18n import DEFAULT_LOCALE, Translator, available_locales


def test_available_locales() -> None:
    locales = available_locales()
    assert locales[0] == DEFAULT_LOCALE
    assert "en" in locales


def test_translate_pt_br() -> None:
    tr = Translator("pt-BR")
    assert tr.t("title") == "Título"


def test_translate_en() -> None:
    tr = Translator("en")
    assert tr.t("title") == "Title"


def test_unknown_locale_falls_back() -> None:
    tr = Translator("xx-YY")
    assert tr.locale == DEFAULT_LOCALE


def test_unknown_key_returns_key() -> None:
    tr = Translator("en")
    assert tr.t("nonexistent_key") == "nonexistent_key"
