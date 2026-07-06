"""Testes de contratos, cliente fake e utilitários de LLM."""

from __future__ import annotations

import json

import pytest

from copamind.llm.client import FakeLLMClient, LLMError, extract_json
from copamind.llm.config import load_model_specs
from copamind.llm.contracts import AnalystResponse


def test_extract_json_with_surrounding_text() -> None:
    text = 'blá blá {"model_role": "x", "answer": "oi"} fim'
    assert extract_json(text)["answer"] == "oi"


def test_extract_json_invalid() -> None:
    with pytest.raises(LLMError):
        extract_json("sem json aqui")


def test_analyst_response_defaults() -> None:
    resp = AnalystResponse(model_role="primary_analyst", answer="texto")
    assert resp.confidence == "medium"
    assert resp.agrees_with_statistical_model is True
    assert resp.claims == []


def test_fake_client_and_unload() -> None:
    client = FakeLLMClient({"m1": json.dumps({"model_role": "r", "answer": "a"})})
    raw = client.complete(messages=[], model_id="m1")
    assert raw.model_id == "m1"
    client.unload("m1")
    assert client.unloaded == ["m1"]


def test_fake_client_unknown_model() -> None:
    client = FakeLLMClient({})
    with pytest.raises(LLMError):
        client.complete(messages=[], model_id="x")


def test_load_model_specs_from_example() -> None:
    specs = load_model_specs("config/models.example.yaml")
    assert set(specs) == {"analyst", "challenger", "auditor"}
    assert specs["auditor"].temperature == 0.0
