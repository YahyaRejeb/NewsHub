from __future__ import annotations

import json
import os
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        host: str | None = None,
        generation_model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        self.generation_model = generation_model or os.getenv("OLLAMA_MODEL") or "qwen3:14b"
        self.embedding_model = embedding_model or os.getenv("OLLAMA_EMBED_MODEL") or "nomic-embed-text"
        self.generation_model_candidates = self._build_generation_model_candidates(self.generation_model)
        self._cached_model_names: list[str] = []
        self._model_cache_expires_at = 0.0

    def is_available(self) -> bool:
        try:
            self._get("/api/version", timeout=6)
            return True
        except OllamaError:
            return False

    def list_models(self, force_refresh: bool = False) -> list[str]:
        now = time.monotonic()
        if not force_refresh and self._cached_model_names and now < self._model_cache_expires_at:
            return list(self._cached_model_names)

        response = self._get("/api/tags", timeout=6)
        models = response.get("models")
        if not isinstance(models, list):
            raise OllamaError("Ollama returned an invalid model list.")

        names = []
        for model in models:
            if not isinstance(model, dict):
                continue
            name = model.get("name") or model.get("model")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())

        self._cached_model_names = names
        self._model_cache_expires_at = now + 30
        return list(names)

    def resolve_generation_model(self, force_refresh: bool = False) -> str:
        model_names = self.list_models(force_refresh=force_refresh)
        resolved = self._select_generation_model(model_names)
        if resolved:
            return resolved

        if not force_refresh:
            return self.resolve_generation_model(force_refresh=True)

        available = ", ".join(model_names[:8]) if model_names else "none"
        raise OllamaError(
            "No installed Qwen3 model is available. "
            f"Expected one of {', '.join(self.generation_model_candidates)}, but found {available}."
        )

    def resolve_embedding_model(self, force_refresh: bool = False) -> str:
        model_names = self.list_models(force_refresh=force_refresh)
        resolved = self._find_installed_model_name(self.embedding_model, model_names)
        if resolved:
            return resolved

        if not force_refresh:
            return self.resolve_embedding_model(force_refresh=True)

        raise OllamaError(
            f"The embedding model `{self.embedding_model}` is not installed in Ollama."
        )

    def runtime_status(self) -> dict[str, Any]:
        issues: list[str] = []
        installed_models: list[str] = []
        active_generation_model: str | None = None
        connected = self.is_available()

        if connected:
            try:
                installed_models = self.list_models(force_refresh=True)
            except OllamaError as exc:
                issues.append(
                    f"Ollama is online, but NewsHub could not read the installed models: {exc}"
                )
        else:
            issues.append(
                f"Ollama is not reachable at {self.host}. Start Ollama and keep the local API running."
            )

        if installed_models:
            try:
                active_generation_model = self.resolve_generation_model(force_refresh=False)
            except OllamaError as exc:
                issues.append(str(exc))
        elif connected:
            issues.append("Ollama is online, but no models were reported by `/api/tags`.")

        retrieval_ready = False
        if installed_models:
            retrieval_ready = bool(self._find_installed_model_name(self.embedding_model, installed_models))
            if not retrieval_ready:
                issues.append(
                    f"The embedding model `{self.embedding_model}` is missing, so retrieval falls back to keyword matching."
                )
        elif connected:
            issues.append(
                f"The embedding model `{self.embedding_model}` could not be verified because no installed models were returned."
            )

        return {
            "host": self.host,
            "preferredGenerationModel": self.generation_model,
            "activeGenerationModel": active_generation_model,
            "embeddingModel": self.embedding_model,
            "connected": connected,
            "generalReady": bool(active_generation_model),
            "articleBriefReady": True,
            "retrievalReady": retrieval_ready,
            "installedModels": installed_models,
            "issues": issues,
        }

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> str:
        payload = {
            "model": self.resolve_generation_model(),
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

        model_name = self.embedding_model
        try:
            model_name = self.resolve_embedding_model()
        except OllamaError:
            pass

        try:
            response = self._post(
                "/api/embed",
                {"model": model_name, "input": texts},
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
                {"model": model_name, "prompt": text},
                timeout=60,
            )
            embedding = response.get("embedding")
            if not isinstance(embedding, list):
                raise OllamaError("Embedding response was missing the vector payload.")
            results.append(embedding)
        return results

    def _build_generation_model_candidates(self, preferred_model: str) -> list[str]:
        family_name = preferred_model.split(":", 1)[0]
        candidates = [preferred_model]

        if family_name == "qwen3":
            candidates.extend(["qwen3", "qwen3:8b", "qwen3:4b"])
        elif family_name:
            candidates.append(family_name)

        deduped: list[str] = []
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in deduped:
                deduped.append(normalized)
        return deduped

    def _select_generation_model(self, model_names: list[str]) -> str | None:
        for candidate in self.generation_model_candidates:
            match = self._find_installed_model_name(candidate, model_names)
            if match:
                return match

        family_name = self.generation_model.split(":", 1)[0]
        family_models = [
            name for name in model_names
            if name == family_name or name.startswith(f"{family_name}:")
        ]
        if not family_models:
            return None

        preferred_size = self._extract_model_size_billions(self.generation_model)
        family_models.sort(
            key=lambda name: (
                abs((self._extract_model_size_billions(name) or preferred_size or 0) - (preferred_size or 0)),
                0 if name == family_name or name.endswith(":latest") else 1,
                name,
            )
        )
        return family_models[0]

    def _find_installed_model_name(self, requested: str, model_names: list[str]) -> str | None:
        normalized_requested = requested.strip()
        if not normalized_requested:
            return None

        if normalized_requested in model_names:
            return normalized_requested

        latest_variant = f"{normalized_requested}:latest"
        if latest_variant in model_names:
            return latest_variant

        if normalized_requested.endswith(":latest"):
            base_name = normalized_requested[: -len(":latest")]
            if base_name in model_names:
                return base_name

        base_name = normalized_requested.split(":", 1)[0]
        if base_name == normalized_requested:
            for model_name in model_names:
                if model_name.startswith(f"{base_name}:"):
                    return model_name
        else:
            requested_tag = normalized_requested.split(":", 1)[1]
            for model_name in model_names:
                if model_name.startswith(f"{base_name}:{requested_tag}"):
                    return model_name

        return None

    def _extract_model_size_billions(self, model_name: str) -> float | None:
        match = re.search(r":(\d+(?:\.\d+)?)b", model_name.lower())
        if not match:
            return None
        return float(match.group(1))

    def _get(self, path: str, timeout: int) -> dict[str, Any]:
        return self._request(path=path, payload=None, timeout=timeout, method="GET")

    def _post(self, path: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        return self._request(path=path, payload=payload, timeout=timeout, method="POST")

    def _request(
        self,
        path: str,
        payload: dict[str, Any] | None,
        timeout: int,
        method: str,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.host}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method=method,
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
