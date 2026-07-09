"""Testes de contratos, cliente fake e utilitários de LLM."""

from __future__ import annotations

import json

import httpx
import pytest

from copamind.llm.client import FakeLLMClient, LLMError, LMStudioClient, extract_json
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


def test_lmstudio_payloads_prefer_structured_json() -> None:
    client = LMStudioClient()
    payloads = client._payloads("m1", [], 0.2, {"type": "object"})
    assert [mode for mode, _ in payloads] == ["json_schema", "json_object", "text"]
    assert payloads[0][1]["response_format"]["type"] == "json_schema"


def test_lmstudio_falls_back_from_unsupported_json_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(
        url: str,
        *,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        calls.append(json)
        request = httpx.Request("POST", url)
        if len(calls) == 1:
            return httpx.Response(400, json={"error": "unsupported"}, request=request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"answer": "ok"}'}}], "usage": {}},
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    raw = LMStudioClient().complete(
        messages=[],
        model_id="m1",
        response_schema={"type": "object"},
    )
    assert raw.content == '{"answer": "ok"}'
    assert [item["mode"] for item in raw.attempts] == ["json_schema", "json_object"]


