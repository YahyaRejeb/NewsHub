from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ArticleInput:
    title: str = ""
    description: str = ""
    content: str = ""
    image_url: str | None = None
    source_url: str = ""
    source_name: str = ""
    published_at: str | None = None
    category: str | None = None
    datatype: str | None = None
    country: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ArticleInput":
        return cls(
            title=(payload.get("title") or "").strip(),
            description=(payload.get("description") or "").strip(),
            content=(payload.get("content") or "").strip(),
            image_url=payload.get("image_url"),
            source_url=(payload.get("source_url") or "").strip(),
            source_name=(payload.get("source_name") or "").strip(),
            published_at=payload.get("published_at"),
            category=payload.get("category"),
            datatype=payload.get("datatype"),
            country=payload.get("country"),
        )

    def cache_key(self) -> str:
        return (self.source_url or f"{self.title}::{self.source_name}").strip().lower()

    def best_available_text(self) -> str:
        return self.content or self.description or self.title

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChatTurn:
    role: str
    content: str
    mode: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ArticleChunk:
    chunk_id: str
    text: str
    token_count: int
    start_index: int
    end_index: int
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExtractedArticle:
    title: str
    source_url: str
    source_name: str
    published_at: str | None
    summary_hint: str
    content: str
    extraction_sources: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ArticleMemory:
    title: str
    source_name: str
    published_at: str | None
    summary: str
    long_summary: str
    why_it_matters: str
    key_facts: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    places: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    important_numbers: list[str] = field(default_factory=list)
    timeline: list[str] = field(default_factory=list)
    suggested_questions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalEvidence:
    chunk_id: str
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalResult:
    evidence: list[RetrievalEvidence]
    confidence: float
    weak_evidence: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": [item.to_dict() for item in self.evidence],
            "confidence": self.confidence,
            "weak_evidence": self.weak_evidence,
        }
