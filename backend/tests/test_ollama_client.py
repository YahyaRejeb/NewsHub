from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chatbot.ollama_client import OllamaClient, OllamaError


class StaticOllamaClient(OllamaClient):
    def __init__(
        self,
        model_names: list[str],
        *,
        generation_model: str = "qwen3:14b",
        embedding_model: str = "nomic-embed-text",
        connected: bool = True,
    ) -> None:
        super().__init__(
            host="http://127.0.0.1:11434",
            generation_model=generation_model,
            embedding_model=embedding_model,
        )
        self._model_names = list(model_names)
        self._connected = connected

    def is_available(self) -> bool:
        return self._connected

    def list_models(self, force_refresh: bool = False) -> list[str]:
        if not self._connected:
            raise OllamaError("offline")
        return list(self._model_names)


class OllamaClientTests(unittest.TestCase):
    def test_resolve_generation_model_prefers_exact_match(self) -> None:
        client = StaticOllamaClient(["qwen3:14b", "nomic-embed-text:latest"])

        self.assertEqual(client.resolve_generation_model(), "qwen3:14b")

    def test_resolve_generation_model_accepts_latest_alias(self) -> None:
        client = StaticOllamaClient(
            ["qwen3:latest", "nomic-embed-text:latest"],
            generation_model="qwen3",
        )

        self.assertEqual(client.resolve_generation_model(), "qwen3:latest")

    def test_resolve_generation_model_accepts_quantized_variant(self) -> None:
        client = StaticOllamaClient(["qwen3:14b-q8_0", "nomic-embed-text:latest"])

        self.assertEqual(client.resolve_generation_model(), "qwen3:14b-q8_0")

    def test_resolve_generation_model_falls_back_to_other_qwen3_variant(self) -> None:
        client = StaticOllamaClient(["qwen3:8b", "nomic-embed-text:latest"])

        self.assertEqual(client.resolve_generation_model(), "qwen3:8b")

    def test_runtime_status_reports_connection_and_embedding_alias(self) -> None:
        client = StaticOllamaClient(["qwen3:14b", "nomic-embed-text:latest"])

        status = client.runtime_status()

        self.assertTrue(status["connected"])
        self.assertTrue(status["generalReady"])
        self.assertTrue(status["retrievalReady"])
        self.assertEqual(status["activeGenerationModel"], "qwen3:14b")

    def test_runtime_status_reports_offline_ollama(self) -> None:
        client = StaticOllamaClient([], connected=False)

        status = client.runtime_status()

        self.assertFalse(status["connected"])
        self.assertFalse(status["generalReady"])
        self.assertGreaterEqual(len(status["issues"]), 1)


if __name__ == "__main__":
    unittest.main()
