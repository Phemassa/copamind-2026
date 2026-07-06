"""Clientes de LLM local (LM Studio / Ollama) e um cliente fake para testes.

Saída estruturada: o cliente pede JSON e o chamador valida com Pydantic. Todo
documento/evidência é tratado como dado não confiável (proteção contra injeção).
"""

from __future__ import annotations

import json
import time
from typing import Protocol

import httpx
from pydantic import BaseModel


class LLMError(Exception):
    """Falha ao chamar um LLM local."""


class LLMResponse(BaseModel):
    """Resposta bruta de um LLM."""

    content: str
    model_id: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    @property
    def tokens_per_second(self) -> float | None:
        """Tokens de sa\u00edda por segundo, se dispon\u00edvel."""
        if self.completion_tokens is None or self.latency_ms <= 0:
            return None
        return self.completion_tokens / (self.latency_ms / 1000.0)


def extract_json(text: str) -> dict[str, object]:
    """Extrai o primeiro objeto JSON de um texto (robusto a texto ao redor)."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMError("resposta não contém JSON")
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"JSON inválido: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LLMError("JSON não é um objeto")
    return parsed


class LLMClient(Protocol):
    """Interface de um cliente de LLM local."""

    def complete(
        self,
        *,
        messages: list[dict[str, str]],
        model_id: str,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Gera uma resposta a partir das mensagens."""
        ...

    def unload(self, model_id: str) -> None:
        """Descarrega o modelo da memória (quando suportado)."""
        ...


class FakeLLMClient:
    """Cliente determinístico para testes.

    Mapeia ``model_id`` -> conteúdo (string JSON). Registra unloads.
    """

    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = responses
        self.unloaded: list[str] = []

    def complete(
        self,
        *,
        messages: list[dict[str, str]],
        model_id: str,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if model_id not in self._responses:
            raise LLMError(f"modelo não configurado no fake: {model_id}")
        content = self._responses[model_id]
        return LLMResponse(
            content=content,
            model_id=model_id,
            latency_ms=1.0,
            prompt_tokens=10,
            completion_tokens=len(content.split()),
        )

    def unload(self, model_id: str) -> None:
        self.unloaded.append(model_id)


class LMStudioClient:
    """Cliente para LM Studio (API compatível com OpenAI)."""

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
    ) -> LLMResponse:
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        start = time.perf_counter()
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"falha na chamada ao LM Studio: {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000.0
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model_id=model_id,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    def unload(self, model_id: str) -> None:
        # A API OpenAI do LM Studio não expõe unload padrão; no-op seguro.
        return None


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
        return LLMResponse(
            content=data["message"]["content"],
            model_id=model_id,
            latency_ms=latency_ms,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
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
