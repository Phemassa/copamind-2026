"""Clientes de LLM local (LM Studio / Ollama) e um cliente fake para testes."""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field


class LLMError(Exception):
    """Falha ao chamar um LLM local."""


class LLMResponse(BaseModel):
    """Resposta bruta de um LLM."""

    content: str
    model_id: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    attempts: list[dict[str, object]] = Field(default_factory=list)

    @property
    def tokens_per_second(self) -> float | None:
        """Tokens de saida por segundo, se disponivel."""
        if self.completion_tokens is None or self.latency_ms <= 0:
            return None
        return self.completion_tokens / (self.latency_ms / 1000.0)


def extract_json(text: str) -> dict[str, object]:
    """Extrai o primeiro objeto JSON de um texto."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMError("resposta nao contem JSON")
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"JSON invalido: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LLMError("JSON nao e um objeto")
    return parsed


class LLMClient(Protocol):
    """Interface de um cliente de LLM local."""

    def complete(
        self,
        *,
        messages: list[dict[str, str]],
        model_id: str,
        temperature: float = 0.2,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Gera uma resposta a partir das mensagens."""
        ...

    def unload(self, model_id: str) -> None:
        """Descarrega o modelo da memoria quando suportado."""
        ...


class FakeLLMClient:
    """Cliente deterministico para testes."""

    def __init__(self, responses: dict[str, str | list[str]]) -> None:
        self._responses = responses
        self.unloaded: list[str] = []
        self.calls: list[dict[str, object]] = []

    def complete(
        self,
        *,
        messages: list[dict[str, str]],
        model_id: str,
        temperature: float = 0.2,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        if model_id not in self._responses:
            raise LLMError(f"modelo nao configurado no fake: {model_id}")
        self.calls.append(
            {
                "model_id": model_id,
                "temperature": temperature,
                "response_schema": response_schema is not None,
                "messages": messages,
            }
        )
        value = self._responses[model_id]
        if isinstance(value, list):
            if not value:
                content = ""
            elif len(value) == 1:
                content = value[0]
            else:
                content = value.pop(0)
        else:
            content = value
        return LLMResponse(
            content=content,
            model_id=model_id,
            latency_ms=1.0,
            prompt_tokens=10,
            completion_tokens=len(content.split()),
            attempts=[{"mode": "fake", "ok": True}],
        )

    def unload(self, model_id: str) -> None:
        self.unloaded.append(model_id)


class LMStudioClient:
    """Cliente para LM Studio (API compativel com OpenAI)."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "lm-studio",
        timeout: float = 300.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def complete(
        self,
        *,
        messages: list[dict[str, str]],
        model_id: str,
        temperature: float = 0.2,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        payloads = self._payloads(model_id, messages, temperature, response_schema)
        start = time.perf_counter()
        attempts: list[dict[str, object]] = []
        last_error: Exception | None = None
        data: dict[str, Any] | None = None

        for mode, payload in payloads:
            try:
                response = httpx.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=self._timeout,
                )
                response.raise_for_status()
                data = response.json()
                attempts.append({"mode": mode, "ok": True})
                break
            except httpx.HTTPStatusError as exc:
                body = exc.response.text.lower()
                is_backend_crash = "channel error" in body
                attempts.append(
                    {
                        "mode": mode,
                        "ok": False,
                        "status_code": exc.response.status_code,
                        "error": str(exc),
                        "backend_crash": is_backend_crash,
                    }
                )
                last_error = exc
                if exc.response.status_code not in {400, 404, 422} or is_backend_crash:
                    break
            except httpx.HTTPError as exc:
                attempts.append({"mode": mode, "ok": False, "error": str(exc)})
                last_error = exc
                break

        if data is None:
            raise LLMError(f"falha na chamada ao LM Studio: {last_error}") from last_error

        latency_ms = (time.perf_counter() - start) * 1000.0
        msg = data["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning_content") or ""
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model_id=model_id,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            attempts=attempts,
        )

    def list_models(self) -> list[str]:
        """Lista modelos expostos pelo LM Studio local."""
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            response = httpx.get(
                f"{self._base_url}/models",
                headers=headers,
                timeout=min(self._timeout, 30.0),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"falha ao listar modelos no LM Studio: {exc}") from exc
        data = response.json()
        return [str(item["id"]) for item in data.get("data", []) if item.get("id")]

    def unload(self, model_id: str) -> None:
        return None

    def _payloads(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        temperature: float,
        response_schema: dict[str, Any] | None,
    ) -> list[tuple[str, dict[str, Any]]]:
        base: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
        }
        payloads: list[tuple[str, dict[str, Any]]] = []
        if response_schema is not None:
            payloads.append(
                (
                    "json_schema",
                    base
                    | {
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "copamind_bolao_pick",
                                "schema": response_schema,
                                "strict": True,
                            },
                        }
                    },
                )
            )
            payloads.append(("json_object", base | {"response_format": {"type": "json_object"}}))
        payloads.append(("text", base))
        return payloads


class OllamaClient:
    """Cliente para Ollama (com unload via keep_alive=0)."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 300.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def complete(
        self,
        *,
        messages: list[dict[str, str]],
        model_id: str,
        temperature: float = 0.2,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }
        start = time.perf_counter()
        try:
            response = httpx.post(f"{self._base_url}/api/chat", json=payload, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"falha na chamada ao Ollama: {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000.0
        data = response.json()
        ollama_msg = data["message"]
        return LLMResponse(
            content=ollama_msg.get("content") or ollama_msg.get("thinking") or "",
            model_id=model_id,
            latency_ms=latency_ms,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            attempts=[{"mode": "ollama_json", "ok": True}],
        )

    def unload(self, model_id: str) -> None:
        try:
            httpx.post(
                f"{self._base_url}/api/generate",
                json={"model": model_id, "keep_alive": 0},
                timeout=30.0,
            )
        except httpx.HTTPError:
            return None
