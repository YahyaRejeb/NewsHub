from __future__ import annotations

import math
import re

from chatbot.types import ArticleChunk, RetrievalEvidence, RetrievalResult

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
}
WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")


def rank_chunks(
    question: str,
    chunks: list[ArticleChunk],
    query_embedding: list[float] | None,
    top_k: int = 4,
) -> RetrievalResult:
    scored_items: list[tuple[float, ArticleChunk]] = []
    query_terms = _keywords(question)

    for chunk in chunks:
        lexical = _lexical_overlap(query_terms, chunk.text)
        cosine = _cosine_similarity(query_embedding, chunk.embedding)
        score = cosine * 0.85 + lexical * 0.15 if query_embedding and chunk.embedding else lexical

        if score <= 0:
            continue

        scored_items.append((score, chunk))

    scored_items.sort(key=lambda item: item[0], reverse=True)
    top_items = scored_items[:top_k]

    evidence = [
        RetrievalEvidence(
            chunk_id=chunk.chunk_id,
            text=_truncate(chunk.text),
            score=round(score, 3),
        )
        for score, chunk in top_items
    ]

    if not top_items:
        return RetrievalResult(evidence=[], confidence=0.0, weak_evidence=True)

    top_score = top_items[0][0]
    average_score = sum(score for score, _ in top_items) / len(top_items)
    confidence = round(min(1.0, top_score * 0.7 + average_score * 0.3), 3)
    weak_threshold = 0.46 if query_embedding else 0.18
    weak_evidence = top_score < weak_threshold or confidence < weak_threshold

    return RetrievalResult(
        evidence=evidence,
        confidence=confidence,
        weak_evidence=weak_evidence,
    )


def _keywords(text: str) -> set[str]:
    return {
        token.lower()
        for token in WORD_PATTERN.findall(text or "")
        if len(token) > 2 and token.lower() not in STOPWORDS
    }


def _lexical_overlap(query_terms: set[str], chunk_text: str) -> float:
    if not query_terms:
        return 0.0

    chunk_terms = _keywords(chunk_text)
    if not chunk_terms:
        return 0.0

    overlap = len(query_terms & chunk_terms)
    return overlap / max(len(query_terms), 1)


def _cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    numerator = sum(a * b for a, b in zip(left, right))
    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))

    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0

    return numerator / (left_magnitude * right_magnitude)


def _truncate(text: str, limit: int = 320) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
