from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chatbot.html_utils import extract_article_payload
from chatbot.ollama_client import OllamaError
from chatbot.service import NewsAssistantService
from chatbot.types import ArticleInput


ARTICLE_TEXT = (
    "Acme Bank announced on Monday that it will acquire Beacon Finance for $2.4 billion. "
    "Chief executive Maya Lopez said the deal is expected to close in September after regulatory review. "
    "The companies said the merger will expand lending access across Chicago, New York, and Dallas. "
    "Analysts said the acquisition could reshape competition in regional banking."
)


class FakeOllamaClient:
    def __init__(self, *, general_answer: str = "Here is a general answer.", fail_chat: bool = True):
        self.general_answer = general_answer
        self.fail_chat = fail_chat

    def chat(self, messages, temperature=0.2, max_tokens=500):  # noqa: ANN001
        prompt = " ".join(item.get("content", "") for item in messages)
        if "general assistant" in prompt.lower():
            return self.general_answer
        if self.fail_chat:
            raise OllamaError("chat unavailable")
        return (
            '{"summary":"Acme Bank plans to buy Beacon Finance.","long_summary":"Acme Bank plans to buy '
            'Beacon Finance for $2.4 billion and says the deal should close in September. The merger would '
            'expand lending access across Chicago, New York, and Dallas.","why_it_matters":"The acquisition '
            'could reshape regional banking competition.","key_facts":["Acme Bank is acquiring Beacon Finance.",'
            '"The deal is valued at $2.4 billion."],"people":["Maya Lopez"],"organizations":["Acme Bank",'
            '"Beacon Finance"],"places":["Chicago","New York","Dallas"],"dates":["Monday","September"],'
            '"important_numbers":["$2.4 billion"],"timeline":["Announcement on Monday.","Expected close in '
            'September."],"suggested_questions":["What are the key facts?"]}'
        )

    def embed_texts(self, texts):  # noqa: ANN001
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "capital of japan" in lowered or "capital" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            elif "acquire" in lowered or "bank" in lowered or "finance" in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif "weather" in lowered or "sports" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.2, 0.1, 0.1])
        return vectors


class WeakOverviewOllamaClient(FakeOllamaClient):
    def embed_texts(self, texts):  # noqa: ANN001
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "acme bank announced" in lowered or "beacon finance" in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif "summarize this article" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            elif "weather" in lowered or "capital of japan" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.1, 0.1, 0.1])
        return vectors


class MemoryCache:
    def __init__(self):
        self.store = {}

    def get(self, namespace, key):  # noqa: ANN001
        return self.store.get((namespace, key))

    def set(self, namespace, key, value, ttl_seconds):  # noqa: ANN001
        self.store[(namespace, key)] = value
        return value


def fake_extractor(_article):  # noqa: ANN001
    return {
        "title": "Acme Bank to acquire Beacon Finance",
        "source_url": "https://example.com/news/acme-beacon",
        "source_name": "Example News",
        "published_at": "2026-04-20T10:00:00Z",
        "summary_hint": "Acme Bank announced a major acquisition.",
        "content": ARTICLE_TEXT,
        "extraction_sources": ["json-ld", "article-paragraphs"],
        "limitations": [],
        "blocked": False,
    }


def blocked_extractor(_article):  # noqa: ANN001
    payload = fake_extractor(_article)
    payload["blocked"] = True
    payload["limitations"] = [
        "The source page could not be fetched directly, so the assistant relied on content already stored in the app."
    ]
    return payload


class NewsAssistantServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = MemoryCache()
        self.article_payload = {
            "title": "Acme Bank to acquire Beacon Finance",
            "description": "Acme Bank announced a major acquisition.",
            "content": ARTICLE_TEXT,
            "source_url": "https://example.com/news/acme-beacon",
            "source_name": "Example News",
            "published_at": "2026-04-20T10:00:00Z",
            "category": "business",
        }

    def build_service(self, *, extractor=fake_extractor, fail_chat=True, ollama_client=None) -> NewsAssistantService:
        return NewsAssistantService(
            cache=self.cache,
            ollama_client=ollama_client or FakeOllamaClient(fail_chat=fail_chat),
            extractor=extractor,
        )

    def test_article_brief_contains_summary_long_summary_and_why_it_matters(self) -> None:
        service = self.build_service()

        brief = service.get_article_brief(self.article_payload)

        self.assertTrue(brief["summary"])
        self.assertTrue(brief["longSummary"])
        self.assertTrue(brief["whyItMatters"])
        self.assertGreaterEqual(len(brief["keyPoints"]), 1)

    def test_unrelated_question_uses_general_route(self) -> None:
        service = self.build_service(fail_chat=False)

        reply = service.ask(self.article_payload, "What is the capital of Japan?", [])

        self.assertEqual(reply["route"], "general_unrelated")
        self.assertEqual(reply["mode"], "general")

    def test_simple_command_is_answered_directly(self) -> None:
        service = self.build_service()

        reply = service.ask(self.article_payload, "count from 1 to 5", [])

        self.assertEqual(reply["route"], "simple_command")
        self.assertEqual(reply["answer"], "1, 2, 3, 4, 5")

    def test_weak_evidence_adds_limitation(self) -> None:
        service = self.build_service()

        reply = service.ask(self.article_payload, "What does the article say about tomorrow's weather?", [])

        self.assertEqual(reply["mode"], "grounded")
        self.assertTrue(any("limited" in item.lower() for item in reply["limitations"]))

    def test_blocked_article_surfaces_fallback_state(self) -> None:
        service = self.build_service(extractor=blocked_extractor)

        brief = service.get_article_brief(self.article_payload)

        self.assertTrue(brief["blocked"])
        self.assertTrue(any("relied on content already stored in the app" in item for item in brief["limitations"]))

    def test_repeated_question_uses_cached_answer(self) -> None:
        service = self.build_service()

        first_reply = service.ask(self.article_payload, "What are the key facts in this story?", [])
        second_reply = service.ask(self.article_payload, "What are the key facts in this story?", [])

        self.assertFalse(first_reply["cached"])
        self.assertTrue(second_reply["cached"])

    def test_invalid_source_url_falls_back_to_app_content(self) -> None:
        extracted = extract_article_payload(
            ArticleInput(
                title="Broken link story",
                description="Fallback summary",
                content="Fallback body content from the app.",
                source_url="#",
                source_name="Example News",
            )
        )

        self.assertEqual(extracted["content"], "Fallback body content from the app.")
        self.assertTrue(any("invalid" in item.lower() for item in extracted["limitations"]))

    def test_unrelated_follow_up_after_article_history_reroutes_to_general(self) -> None:
        service = self.build_service(fail_chat=False)
        history = [
            {"role": "user", "content": "Summarize this article.", "mode": "grounded"},
            {"role": "assistant", "content": "Acme Bank plans to buy Beacon Finance.", "mode": "grounded"},
        ]

        reply = service.ask(self.article_payload, "What is the capital of Japan?", history)

        self.assertEqual(reply["route"], "general_unrelated")
        self.assertEqual(reply["mode"], "general")

    def test_article_overview_prompt_is_not_marked_weak_when_article_text_exists(self) -> None:
        service = self.build_service(
            fail_chat=False,
            ollama_client=WeakOverviewOllamaClient(fail_chat=False),
        )

        reply = service.ask(self.article_payload, "Summarize this article for me.", [])

        self.assertEqual(reply["mode"], "grounded")
        self.assertFalse(any("limited" in item.lower() for item in reply["limitations"]))
        self.assertGreaterEqual(len(reply["evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
