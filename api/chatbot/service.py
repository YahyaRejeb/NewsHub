from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from chatbot.cache_layer import DiskTTLCache
from chatbot.chunker import build_chunks
from chatbot.html_utils import extract_article_payload
from chatbot.ollama_client import OllamaClient, OllamaError
from chatbot.retrieval import rank_chunks
from chatbot.router import classify_message, execute_simple_command
from chatbot.types import (
    ArticleChunk,
    ArticleInput,
    ArticleMemory,
    ChatTurn,
    ExtractedArticle,
    RetrievalEvidence,
    RetrievalResult,
)

ARTICLE_TTL_SECONDS = 24 * 60 * 60
BRIEF_TTL_SECONDS = 24 * 60 * 60
QA_TTL_SECONDS = 60 * 60
MAX_HISTORY_TURNS = 6
MAX_ARTICLE_PROMPT_CHARS = 12000
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
NUMBER_PATTERN = re.compile(r"\b\d[\d,]*(?:\.\d+)?%?\b")
DATE_PATTERN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|"
    r"Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b[^.?!,\n]{0,30}",
    re.IGNORECASE,
)
ENTITY_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b")
TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
ARTICLE_CONTEXT_TERMS = (
    "article",
    "story",
    "headline",
    "report",
    "coverage",
    "this",
    "that",
    "it",
    "they",
    "them",
    "again",
    "more",
    "simply",
)
OVERVIEW_PROMPT_TERMS = (
    "summarize",
    "summary",
    "key facts",
    "what happened",
    "why does it matter",
    "why it matters",
    "explain simply",
    "explain this",
    "who is involved",
    "who's involved",
    "what should i know",
)
GENERAL_KNOWLEDGE_PREFIXES = (
    "what is ",
    "who is ",
    "where is ",
    "when is ",
    "how do ",
    "how can ",
    "define ",
    "tell me about ",
)
GENERAL_KNOWLEDGE_TERMS = (
    "capital of",
    "weather",
    "recipe",
    "translate",
    "joke",
    "meaning of",
)


class NewsAssistantService:
    def __init__(
        self,
        cache: DiskTTLCache | None = None,
        ollama_client: OllamaClient | None = None,
        extractor: Callable[[ArticleInput], dict[str, Any]] | None = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parent.parent / ".cache" / "chatbot"
        self.cache = cache or DiskTTLCache(base_dir)
        self.ollama_client = ollama_client or OllamaClient()
        self.extractor = extractor or extract_article_payload

    def get_article_brief(self, article_payload: dict[str, Any]) -> dict[str, Any]:
        article = ArticleInput.from_payload(article_payload)
        knowledge = self._load_article_knowledge(article)
        brief_cache_key = f"{article.cache_key()}::brief"
        cached = self.cache.get("article_briefs", brief_cache_key)
        if cached:
            return cached

        brief = {
            "title": knowledge["memory"].title,
            "sourceName": knowledge["memory"].source_name,
            "publishedAt": knowledge["memory"].published_at,
            "summary": knowledge["memory"].summary,
            "longSummary": knowledge["memory"].long_summary,
            "whyItMatters": knowledge["memory"].why_it_matters,
            "keyPoints": knowledge["memory"].key_facts[:5],
            "people": knowledge["memory"].people[:6],
            "organizations": knowledge["memory"].organizations[:6],
            "places": knowledge["memory"].places[:6],
            "dates": knowledge["memory"].dates[:6],
            "importantNumbers": knowledge["memory"].important_numbers[:6],
            "timeline": knowledge["memory"].timeline[:5],
            "suggestedQuestions": knowledge["memory"].suggested_questions[:4],
            "limitations": knowledge["memory"].limitations,
            "blocked": knowledge["extracted"].blocked,
        }

        return self.cache.set("article_briefs", brief_cache_key, brief, BRIEF_TTL_SECONDS)

    def ask(
        self,
        article_payload: dict[str, Any],
        message: str,
        history_payload: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        history = self._normalize_history(history_payload)
        route = classify_message(message, history)
        stripped_message = (message or "").strip()

        if route == "greeting":
            return {
                "mode": "general",
                "route": route,
                "answer": "Hi, I'm the NewsHub assistant. I can break down this article, surface the key facts, or handle general questions if you want to switch gears.",
                "evidence": [],
                "confidence": 1.0,
                "limitations": [],
                "cached": False,
            }

        if route == "simple_command":
            direct_answer = execute_simple_command(stripped_message)
            return {
                "mode": "general",
                "route": route,
                "answer": direct_answer or "I couldn't complete that command exactly as written.",
                "evidence": [],
                "confidence": 1.0,
                "limitations": [],
                "cached": False,
            }

        article = ArticleInput.from_payload(article_payload)
        qa_cache_key = self._build_qa_cache_key(article, route, stripped_message, history)
        cached = self.cache.get("qa_results", qa_cache_key)
        if cached:
            return {
                **cached,
                "evidence": list(cached.get("evidence", [])),
                "limitations": list(cached.get("limitations", [])),
                "cached": True,
            }

        if route == "general_unrelated":
            response = self._answer_general_question(stripped_message)
            self.cache.set("qa_results", qa_cache_key, response, QA_TTL_SECONDS)
            return response

        knowledge = self._load_article_knowledge(article)
        query_embedding = self._embed_query(stripped_message)
        retrieval = rank_chunks(stripped_message, knowledge["chunks"], query_embedding, top_k=4)
        retrieval = self._normalize_retrieval(stripped_message, route, knowledge["chunks"], retrieval)

        if self._should_reroute_to_general(stripped_message, route, retrieval):
            response = self._answer_general_question(stripped_message)
            self.cache.set("qa_results", qa_cache_key, response, QA_TTL_SECONDS)
            return response

        answer = self._generate_grounded_answer(stripped_message, history, knowledge, retrieval.to_dict())

        if self._is_low_quality(answer, knowledge["memory"].title):
            answer = self._build_grounded_fallback(stripped_message, knowledge["memory"], retrieval.to_dict())

        limitations = list(knowledge["memory"].limitations)
        if retrieval.weak_evidence:
            limitations = ["Article evidence is limited for this question."] + limitations

        response = {
            "mode": "grounded",
            "route": route,
            "answer": answer,
            "evidence": retrieval.to_dict()["evidence"],
            "confidence": retrieval.confidence,
            "limitations": list(dict.fromkeys(limitations)),
            "cached": False,
        }
        self.cache.set("qa_results", qa_cache_key, response, QA_TTL_SECONDS)
        return response

    def _load_article_knowledge(self, article: ArticleInput) -> dict[str, Any]:
        article_cache_key = article.cache_key()
        cached = self.cache.get("article_knowledge", article_cache_key)
        if cached:
            extracted = ExtractedArticle(**cached["extracted"])
            memory = ArticleMemory(**cached["memory"])
            chunks = [ArticleChunk(**chunk) for chunk in cached["chunks"]]
        else:
            extracted_payload = self.extractor(article)
            extracted = ExtractedArticle(**extracted_payload)
            memory = self._build_article_memory(extracted)
            chunks = build_chunks(extracted.content)
            bundle = {
                "extracted": extracted.to_dict(),
                "memory": memory.to_dict(),
                "chunks": [chunk.to_dict() for chunk in chunks],
            }
            self.cache.set("article_knowledge", article_cache_key, bundle, ARTICLE_TTL_SECONDS)

        chunks = self._attach_chunk_embeddings(article_cache_key, chunks)
        return {
            "article": article,
            "extracted": extracted,
            "memory": memory,
            "chunks": chunks,
        }

    def _attach_chunk_embeddings(self, article_cache_key: str, chunks: list[ArticleChunk]) -> list[ArticleChunk]:
        if not chunks:
            return chunks

        cached_embeddings = self.cache.get("article_embeddings", article_cache_key)
        if cached_embeddings and len(cached_embeddings) == len(chunks):
            for chunk, embedding in zip(chunks, cached_embeddings):
                chunk.embedding = embedding
            return chunks

        try:
            embeddings = self.ollama_client.embed_texts([chunk.text for chunk in chunks])
        except OllamaError:
            return chunks

        if len(embeddings) == len(chunks):
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            self.cache.set("article_embeddings", article_cache_key, embeddings, ARTICLE_TTL_SECONDS)

        return chunks

    def _embed_query(self, message: str) -> list[float] | None:
        try:
            embeddings = self.ollama_client.embed_texts([message])
        except OllamaError:
            return None
        return embeddings[0] if embeddings else None

    def _build_article_memory(self, extracted: ExtractedArticle) -> ArticleMemory:
        llm_memory = self._build_article_memory_with_llm(extracted)
        if llm_memory:
            return llm_memory
        return self._build_article_memory_fallback(extracted)

    def _build_article_memory_with_llm(self, extracted: ExtractedArticle) -> ArticleMemory | None:
        prompt = f"""
You are a newsroom analyst. Read the article and return JSON only.

Return an object with exactly these keys:
- summary
- long_summary
- why_it_matters
- key_facts
- people
- organizations
- places
- dates
- important_numbers
- timeline
- suggested_questions

Rules:
- Ground every field in the article text only.
- Keep summary to 2 sentences max.
- Keep long_summary to 4 sentences max.
- Keep why_it_matters to 2 sentences max.
- Keep arrays short, specific, and factual.
- If a field is unclear, return an empty string or empty array.
- Do not add markdown fences or commentary.

Article title: {extracted.title}
Source: {extracted.source_name}
Published at: {extracted.published_at or "Unknown"}
Limitations: {"; ".join(extracted.limitations) or "None"}

Article text:
{self._clip_text(extracted.content, MAX_ARTICLE_PROMPT_CHARS)}
""".strip()

        try:
            raw = self.ollama_client.chat(
                [
                    {
                        "role": "system",
                        "content": "You return strict JSON with no preamble and no <think> tags.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=800,
            )
        except OllamaError:
            return None

        payload = self._extract_json(raw)
        if not payload:
            return None

        return ArticleMemory(
            title=extracted.title,
            source_name=extracted.source_name,
            published_at=extracted.published_at,
            summary=self._clean_text(payload.get("summary")) or self._first_sentence(extracted.summary_hint or extracted.content),
            long_summary=self._clean_text(payload.get("long_summary")) or self._join_sentences(extracted.content, 3),
            why_it_matters=self._clean_text(payload.get("why_it_matters")) or self._default_why_it_matters(extracted),
            key_facts=self._coerce_string_list(payload.get("key_facts"))[:5] or self._extract_key_facts(extracted.content),
            people=self._coerce_string_list(payload.get("people"))[:6],
            organizations=self._coerce_string_list(payload.get("organizations"))[:6],
            places=self._coerce_string_list(payload.get("places"))[:6],
            dates=self._coerce_string_list(payload.get("dates"))[:6],
            important_numbers=self._coerce_string_list(payload.get("important_numbers"))[:6],
            timeline=self._coerce_string_list(payload.get("timeline"))[:5],
            suggested_questions=self._coerce_string_list(payload.get("suggested_questions"))[:4] or self._default_questions(extracted.title),
            limitations=extracted.limitations,
        )

    def _build_article_memory_fallback(self, extracted: ExtractedArticle) -> ArticleMemory:
        people, organizations, places = self._extract_entities(extracted.content)
        dates = self._dedupe_matches(DATE_PATTERN.findall(extracted.content), limit=6)
        important_numbers = self._dedupe_matches(NUMBER_PATTERN.findall(extracted.content), limit=6)

        return ArticleMemory(
            title=extracted.title,
            source_name=extracted.source_name,
            published_at=extracted.published_at,
            summary=self._first_sentence(extracted.summary_hint or extracted.content or extracted.title),
            long_summary=self._join_sentences(extracted.content, 3),
            why_it_matters=self._default_why_it_matters(extracted),
            key_facts=self._extract_key_facts(extracted.content),
            people=people,
            organizations=organizations,
            places=places,
            dates=dates,
            important_numbers=important_numbers,
            timeline=self._extract_timeline(extracted.content),
            suggested_questions=self._default_questions(extracted.title),
            limitations=extracted.limitations,
        )

    def _answer_general_question(self, message: str) -> dict[str, Any]:
        try:
            answer = self.ollama_client.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are NewsHub's general assistant. "
                            "Answer naturally and clearly. Do not force article evidence into unrelated replies. "
                            "Do not return <think> tags."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0.4,
                max_tokens=400,
            )
        except OllamaError:
            answer = (
                "I can handle general questions too, but the local Ollama model is unavailable right now. "
                "Once `qwen3:14b` is running, I can answer open-ended questions here."
            )

        return {
            "mode": "general",
            "route": "general_unrelated",
            "answer": answer,
            "evidence": [],
            "confidence": 0.78 if "unavailable" not in answer else 0.0,
            "limitations": [],
            "cached": False,
        }

    def _generate_grounded_answer(
        self,
        message: str,
        history: list[ChatTurn],
        knowledge: dict[str, Any],
        retrieval: dict[str, Any],
    ) -> str:
        evidence_lines = []
        for index, evidence in enumerate(retrieval["evidence"], start=1):
            evidence_lines.append(f"[{index}] {evidence['text']}")

        history_lines = [f"{turn.role}: {turn.content}" for turn in history[-MAX_HISTORY_TURNS:]]

        prompt = f"""
You are NewsHub's article-grounded assistant.

Answer the user using only the article memory and evidence excerpts below.
Rules:
- Do not invent facts.
- If the evidence is weak or partial, say so clearly.
- Keep the tone natural and human.
- Prefer short paragraphs or concise bullets when useful.
- Do not mention internal chunk IDs.
- Do not output <think> tags.

Article title: {knowledge["memory"].title}
Source: {knowledge["memory"].source_name}
Short summary: {knowledge["memory"].summary}
Why it matters: {knowledge["memory"].why_it_matters}
Key facts: {" | ".join(knowledge["memory"].key_facts[:5])}
Limitations: {"; ".join(knowledge["memory"].limitations) or "None"}
Retrieval confidence: {retrieval["confidence"]}
Weak evidence: {retrieval["weak_evidence"]}

Recent conversation:
{"None" if not history_lines else chr(10).join(history_lines)}

Evidence:
{chr(10).join(evidence_lines) if evidence_lines else "No strong evidence retrieved."}

User question: {message}
""".strip()

        try:
            return self.ollama_client.chat(
                [
                    {
                        "role": "system",
                        "content": "Return only the final answer. Never include hidden reasoning.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )
        except OllamaError:
            return self._build_grounded_fallback(message, knowledge["memory"], retrieval)

    def _build_grounded_fallback(
        self,
        message: str,
        memory: ArticleMemory,
        retrieval: dict[str, Any],
    ) -> str:
        lower_message = message.lower()
        prefix = (
            "I can answer part of that from the article, but the evidence is limited. "
            if retrieval["weak_evidence"]
            else "Based on the article, "
        )

        if self._is_article_overview_prompt(lower_message):
            if "key facts" in lower_message and memory.key_facts:
                return prefix + "the key facts are: " + " ".join(memory.key_facts[:3])
            if "who" in lower_message and (memory.people or memory.organizations):
                involved = memory.people + memory.organizations
                return prefix + "the main people or groups mentioned are " + ", ".join(involved[:6]) + "."
            if "why" in lower_message:
                return prefix + (memory.why_it_matters or memory.summary)
            return prefix + (memory.long_summary or memory.summary)

        if "who" in lower_message and (memory.people or memory.organizations):
            involved = memory.people + memory.organizations
            return prefix + "the main people or groups mentioned are " + ", ".join(involved[:6]) + "."

        if "when" in lower_message and memory.dates:
            return prefix + "the key dates or timing mentioned are " + ", ".join(memory.dates[:4]) + "."

        if "where" in lower_message and memory.places:
            return prefix + "the places mentioned include " + ", ".join(memory.places[:4]) + "."

        if "why" in lower_message:
            return prefix + (memory.why_it_matters or memory.summary)

        evidence = retrieval.get("evidence") or []
        if evidence:
            lead = evidence[0]["text"]
            return prefix + lead

        return prefix + (memory.summary or "the article offers only limited evidence for that question.")

    def _normalize_retrieval(
        self,
        message: str,
        route: str,
        chunks: list[ArticleChunk],
        retrieval: RetrievalResult,
    ) -> RetrievalResult:
        if route not in {"article_question", "follow_up_article_question"}:
            return retrieval

        if not chunks or not self._is_article_overview_prompt(message):
            return retrieval

        evidence = list(retrieval.evidence)
        if not evidence:
            evidence = [
                RetrievalEvidence(
                    chunk_id=chunk.chunk_id,
                    text=self._truncate_evidence(chunk.text),
                    score=0.52,
                )
                for chunk in chunks[:2]
            ]

        if not evidence:
            return retrieval

        confidence_floor = 0.62 if len(chunks) <= 2 else 0.52
        return RetrievalResult(
            evidence=evidence,
            confidence=max(retrieval.confidence, confidence_floor),
            weak_evidence=False,
        )

    def _should_reroute_to_general(self, message: str, route: str, retrieval: RetrievalResult) -> bool:
        if route != "follow_up_article_question" or not retrieval.weak_evidence:
            return False
        if self._message_has_article_context(message) or self._is_article_overview_prompt(message):
            return False
        return self._looks_general_knowledge_prompt(message)

    def _message_has_article_context(self, message: str) -> bool:
        lowered = (message or "").lower()
        tokens = set(TOKEN_PATTERN.findall(lowered))
        for term in ARTICLE_CONTEXT_TERMS:
            if " " in term:
                if term in lowered:
                    return True
            elif term in tokens:
                return True
        return False

    def _is_article_overview_prompt(self, message: str) -> bool:
        lowered = (message or "").lower()
        return any(term in lowered for term in OVERVIEW_PROMPT_TERMS)

    def _looks_general_knowledge_prompt(self, message: str) -> bool:
        lowered = (message or "").strip().lower()
        if any(lowered.startswith(prefix) for prefix in GENERAL_KNOWLEDGE_PREFIXES):
            return True
        return any(term in lowered for term in GENERAL_KNOWLEDGE_TERMS)

    def _truncate_evidence(self, text: str, limit: int = 320) -> str:
        compact = self._clean_text(text)
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3].rstrip() + "..."

    def _extract_entities(self, text: str) -> tuple[list[str], list[str], list[str]]:
        entities = self._dedupe_matches(ENTITY_PATTERN.findall(text), limit=18)
        people: list[str] = []
        organizations: list[str] = []
        places: list[str] = []

        organization_markers = ("Inc", "Corp", "Company", "University", "Agency", "Department", "Bank", "Council", "Committee")
        place_prepositions = ("in ", "at ", "from ", "across ")

        for entity in entities:
            if any(marker in entity for marker in organization_markers):
                organizations.append(entity)
            elif any(f"{prep}{entity.lower()}" in text.lower() for prep in place_prepositions):
                places.append(entity)
            elif len(entity.split()) >= 2:
                people.append(entity)

        return people[:6], organizations[:6], places[:6]

    def _extract_key_facts(self, text: str) -> list[str]:
        sentences = self._sentences(text)
        facts = [sentence for sentence in sentences if len(sentence) > 40]
        return facts[:5]

    def _extract_timeline(self, text: str) -> list[str]:
        sentences = self._sentences(text)
        timeline = [
            sentence
            for sentence in sentences
            if DATE_PATTERN.search(sentence) or any(marker in sentence.lower() for marker in ("after", "before", "later", "earlier", "then"))
        ]
        return timeline[:5]

    def _normalize_history(self, history_payload: list[dict[str, Any]] | None) -> list[ChatTurn]:
        turns: list[ChatTurn] = []
        for item in history_payload or []:
            role = (item.get("role") or "").strip().lower()
            content = (item.get("content") or "").strip()
            mode = (item.get("mode") or "general").strip().lower()
            if role not in {"user", "assistant"} or not content:
                continue
            turns.append(ChatTurn(role=role, content=content, mode=mode))
        return turns[-MAX_HISTORY_TURNS:]

    def _build_qa_cache_key(
        self,
        article: ArticleInput,
        route: str,
        message: str,
        history: list[ChatTurn],
    ) -> str:
        history_fingerprint = json.dumps([turn.to_dict() for turn in history[-MAX_HISTORY_TURNS:]], sort_keys=True)
        return f"{article.cache_key()}::{route}::{message.lower().strip()}::{history_fingerprint}"

    def _extract_json(self, raw_text: str) -> dict[str, Any] | None:
        if not raw_text:
            return None

        trimmed = raw_text.strip()
        candidate = trimmed
        if not trimmed.startswith("{"):
            start = trimmed.find("{")
            end = trimmed.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            candidate = trimmed[start : end + 1]

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    def _coerce_string_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [self._clean_text(item) for item in value if self._clean_text(item)]
        if isinstance(value, str) and value.strip():
            parts = [re.sub(r"^[\s\-\*\u2022]+|[\s\-\*\u2022]+$", "", segment) for segment in value.split("\n")]
            return [part for part in parts if part]
        return []

    def _dedupe_matches(self, items: list[str], limit: int) -> list[str]:
        seen: set[str] = set()
        results: list[str] = []
        for item in items:
            cleaned = self._clean_text(item)
            normalized = cleaned.lower()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            results.append(cleaned)
            if len(results) >= limit:
                break
        return results

    def _sentences(self, text: str) -> list[str]:
        return [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(text or "") if sentence.strip()]

    def _first_sentence(self, text: str) -> str:
        sentences = self._sentences(text)
        return sentences[0] if sentences else ""

    def _join_sentences(self, text: str, count: int) -> str:
        sentences = self._sentences(text)
        return " ".join(sentences[:count]).strip()

    def _clip_text(self, text: str, limit: int) -> str:
        return (text or "")[:limit].strip()

    def _clean_text(self, value: Any) -> str:
        return " ".join(str(value or "").split()).strip()

    def _default_why_it_matters(self, extracted: ExtractedArticle) -> str:
        if extracted.summary_hint:
            return f"This matters because it shapes the bigger context around {extracted.summary_hint.rstrip('.')}."
        return "This matters because it highlights the main development and its potential impact."

    def _default_questions(self, title: str) -> list[str]:
        return [
            "What are the key facts in this story?",
            "Why does this development matter?",
            "Who is most affected here?",
            f"Can you explain {title[:40]} more simply?" if title else "Can you explain this more simply?",
        ]

    def _is_low_quality(self, answer: str, title: str) -> bool:
        cleaned = self._clean_text(answer)
        if len(cleaned.split()) < 10:
            return True

        if cleaned.lower() == self._clean_text(title).lower():
            return True

        sentences = self._sentences(cleaned)
        if len(sentences) >= 2 and len(set(sentence.lower() for sentence in sentences)) == 1:
            return True

        return False
