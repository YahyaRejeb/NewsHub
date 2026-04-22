from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        host: str = "http://127.0.0.1:11434",
        generation_model: str = "qwen3:14b",
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        self.host = host.rstrip("/")
        self.generation_model = generation_model
        self.embedding_model = embedding_model

    def is_available(self) -> bool:
        try:
            self._post("/api/tags", {}, timeout=6)
            return True
        except OllamaError:
            return False

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> str:
        payload = {
            "model": self.generation_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
            },
        }
        response = self._post("/api/chat", payload, timeout=90)
        content = (
            response.get("message", {}).get("content")
            or response.get("response")
            or ""
        )
        cleaned = self._strip_thinking(content)
        if not cleaned:
            raise OllamaError("Ollama returned an empty response.")
        return cleaned

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self._post(
                "/api/embed",
                {"model": self.embedding_model, "input": texts},
                timeout=90,
            )
            embeddings = response.get("embeddings")
            if isinstance(embeddings, list) and embeddings:
                return embeddings
        except OllamaError:
            pass

        results: list[list[float]] = []
        for text in texts:
            response = self._post(
                "/api/embeddings",
                {"model": self.embedding_model, "prompt": text},
                timeout=60,
            )
            embedding = response.get("embedding")
            if not isinstance(embedding, list):
                raise OllamaError("Embedding response was missing the vector payload.")
            results.append(embedding)
        return results

    def _post(self, path: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.host}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                raw_body = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise OllamaError(str(exc)) from exc

        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError as exc:
            raise OllamaError("Failed to decode Ollama JSON response.") from exc

    def _strip_thinking(self, text: str) -> str:
        without_thinking = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE)
        return without_thinking.strip()
