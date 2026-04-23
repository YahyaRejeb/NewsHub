from __future__ import annotations

import re

from chatbot.types import ChatTurn

GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|bonjour|salut|good morning|good afternoon|good evening|yo)\b",
    re.IGNORECASE,
)
COUNT_PATTERN = re.compile(
    r"^count(?:\s+from)?\s+(-?\d+)\s+(?:to|-)\s+(-?\d+)$",
    re.IGNORECASE,
)
REPEAT_PATTERN = re.compile(r"^(?:say|repeat)(?:\s+after\s+me)?[:\s]+(.+)$", re.IGNORECASE)

ARTICLE_PROMPTS = {
    "summarize this",
    "why does it matter",
    "key facts",
    "explain simply",
    "who is involved",
}
ARTICLE_HINTS = (
    "article",
    "story",
    "headline",
    "report",
    "according to",
    "from the article",
    "in this story",
    "in the article",
    "what happened",
    "why did",
    "who is involved",
)
FOLLOW_UP_MARKERS = {
    "it",
    "they",
    "them",
    "this",
    "that",
    "those",
    "these",
    "more",
    "simply",
    "again",
    "why",
    "how",
    "when",
    "where",
    "who",
    "clarify",
}


def classify_message(message: str, history: list[ChatTurn]) -> str:
    normalized = (message or "").strip()
    lowered = normalized.lower()
    word_count = len(lowered.split())

    if not normalized:
        return "greeting"

    if GREETING_PATTERN.match(normalized) and word_count <= 7:
        return "greeting"

    if is_simple_command(normalized):
        return "simple_command"

    if lowered in ARTICLE_PROMPTS:
        return "article_question"

    article_history = any(turn.mode == "grounded" for turn in history[-6:])
    explicit_article = any(hint in lowered for hint in ARTICLE_HINTS)
    question_like = "?" in normalized or lowered.startswith(
        ("who", "what", "when", "where", "why", "how", "summarize", "explain", "tell me", "give me", "list")
    )
    short_follow_up = article_history and word_count <= 12 and any(
        marker in lowered.split() for marker in FOLLOW_UP_MARKERS
    )

    if explicit_article or lowered.startswith(("summarize", "why does", "key facts", "explain simply")):
        return "article_question"

    if article_history and (short_follow_up or (question_like and not explicit_article)):
        return "follow_up_article_question"

    return "general_unrelated"


def is_simple_command(message: str) -> bool:
    normalized = (message or "").strip()
    return bool(COUNT_PATTERN.match(normalized) or REPEAT_PATTERN.match(normalized))


def execute_simple_command(message: str) -> str | None:
    normalized = (message or "").strip()

    count_match = COUNT_PATTERN.match(normalized)
    if count_match:
        start = int(count_match.group(1))
        end = int(count_match.group(2))
        step = 1 if end >= start else -1
        span = abs(end - start) + 1
        if span > 200:
            return "That range is a bit too large for one reply. Try 200 numbers or fewer."
        values = [str(number) for number in range(start, end + step, step)]
        return ", ".join(values)

    repeat_match = REPEAT_PATTERN.match(normalized)
    if repeat_match:
        return repeat_match.group(1).strip()

    return None
