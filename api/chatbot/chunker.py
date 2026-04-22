from __future__ import annotations

import re

from chatbot.types import ArticleChunk

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def estimate_tokens(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def build_chunks(text: str, chunk_size: int = 300, overlap: int = 50) -> list[ArticleChunk]:
    normalized = (text or "").strip()
    if not normalized:
        return []

    segments: list[str] = []
    for paragraph in re.split(r"\n{2,}", normalized):
        clean_paragraph = paragraph.strip()
        if not clean_paragraph:
            continue

        if estimate_tokens(clean_paragraph) <= chunk_size:
            segments.append(clean_paragraph)
            continue

        sentences = [item.strip() for item in SENTENCE_SPLIT_PATTERN.split(clean_paragraph) if item.strip()]
        segments.extend(sentences or [clean_paragraph])

    chunks: list[ArticleChunk] = []
    current_segments: list[str] = []
    current_token_total = 0
    start_index = 0

    for segment in segments:
        segment_tokens = estimate_tokens(segment)
        if current_segments and current_token_total + segment_tokens > chunk_size:
            chunk_text = " ".join(current_segments).strip()
            chunks.append(
                ArticleChunk(
                    chunk_id=f"chunk-{len(chunks) + 1}",
                    text=chunk_text,
                    token_count=estimate_tokens(chunk_text),
                    start_index=start_index,
                    end_index=start_index + len(chunk_text),
                )
            )

            overlap_segments = _collect_overlap(current_segments, overlap)
            current_segments = overlap_segments.copy()
            current_token_total = estimate_tokens(" ".join(current_segments))
            start_index += max(len(chunk_text) - len(" ".join(overlap_segments)), 0)

        if not current_segments:
            start_index = sum(len(chunk.text) for chunk in chunks)

        current_segments.append(segment)
        current_token_total += segment_tokens

    if current_segments:
        chunk_text = " ".join(current_segments).strip()
        chunks.append(
            ArticleChunk(
                chunk_id=f"chunk-{len(chunks) + 1}",
                text=chunk_text,
                token_count=estimate_tokens(chunk_text),
                start_index=start_index,
                end_index=start_index + len(chunk_text),
            )
        )

    return chunks


def _collect_overlap(segments: list[str], overlap: int) -> list[str]:
    if overlap <= 0:
        return []

    result: list[str] = []
    token_total = 0

    for segment in reversed(segments):
        result.insert(0, segment)
        token_total += estimate_tokens(segment)
        if token_total >= overlap:
            break

    return result
