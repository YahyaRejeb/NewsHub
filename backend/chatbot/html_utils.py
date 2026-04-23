from __future__ import annotations

import html
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from chatbot.types import ArticleInput

try:
    from bs4 import BeautifulSoup, Comment  # type: ignore
except ImportError:  # pragma: no cover - optional dependency at runtime
    BeautifulSoup = None
    Comment = None

BOILERPLATE_PATTERNS = (
    "subscribe",
    "sign in",
    "sign up",
    "newsletter",
    "advertisement",
    "advertising",
    "cookie",
    "all rights reserved",
    "privacy policy",
    "terms of service",
    "download the app",
    "follow us",
    "share this article",
    "read more",
    "continue reading",
    "live updates",
    "watch live",
    "listen to article",
)
WHITESPACE_PATTERN = re.compile(r"\s+")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
SCRIPT_PATTERN = re.compile(r"<(script|style|noscript).*?>.*?</\1>", re.DOTALL | re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_PATTERN = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?P<key>[^"\']+)["\'][^>]+content=["\'](?P<value>[^"\']*)["\'][^>]*>',
    re.IGNORECASE,
)


def _is_fetchable_url(url: str) -> bool:
    candidate = (url or "").strip().lower()
    return candidate.startswith("http://") or candidate.startswith("https://")


def _strip_list_markers(text: str) -> str:
    return re.sub(r"^[\s\-\*\u2022]+|[\s\-\*\u2022]+$", "", text or "")


def extract_article_payload(article: ArticleInput) -> dict[str, Any]:
    html_text = ""
    limitations: list[str] = []
    blocked = False

    if _is_fetchable_url(article.source_url):
        html_text, fetch_limitations = fetch_html(article.source_url)
        limitations.extend(fetch_limitations)
        blocked = not bool(html_text)
    elif article.source_url:
        limitations.append("Source URL was invalid, so the assistant used content already stored in the app.")

    structured = _extract_structured_data(html_text) if html_text else {}
    meta = _extract_meta_data(html_text) if html_text else {}
    paragraphs = _extract_article_paragraphs(html_text) if html_text else ""

    extraction_sources: list[str] = []

    title = _pick_first(
        (
            structured.get("title"),
            meta.get("title"),
            article.title,
        ),
        extraction_sources,
        ("json-ld", "meta", "app-fallback"),
    )

    summary_hint = _pick_first(
        (
            structured.get("description"),
            meta.get("description"),
            article.description,
        ),
        extraction_sources,
        ("json-ld", "meta", "app-fallback"),
    )

    content = _pick_first(
        (
            structured.get("content"),
            paragraphs,
            article.content,
            article.description,
            meta.get("description"),
            article.title,
        ),
        extraction_sources,
        ("json-ld", "article-paragraphs", "app-fallback", "app-fallback", "meta", "app-fallback"),
    )

    source_name = _pick_first(
        (
            structured.get("source_name"),
            meta.get("site_name"),
            article.source_name,
        ),
        extraction_sources,
        ("json-ld", "meta", "app-fallback"),
    ) or "Unknown source"

    published_at = _pick_first(
        (
            structured.get("published_at"),
            meta.get("published_at"),
            article.published_at,
        ),
        extraction_sources,
        ("json-ld", "meta", "app-fallback"),
    )

    cleaned_title = clean_article_text(title)
    cleaned_summary = clean_article_text(summary_hint)
    cleaned_content = clean_article_text(content)

    if not cleaned_content:
        cleaned_content = clean_article_text(article.best_available_text())
        limitations.append("Original page offered very limited readable text, so app fallback content was used.")

    if blocked and article.best_available_text():
        limitations.append("The source page could not be fetched directly, so the assistant relied on content already stored in the app.")

    if not structured and not paragraphs and article.best_available_text():
        limitations.append("The original page did not expose rich structured article text, so the assistant used the in-app article preview as fallback.")

    return {
        "title": cleaned_title or clean_article_text(article.title) or "Untitled article",
        "source_url": article.source_url,
        "source_name": clean_article_text(source_name) or "Unknown source",
        "published_at": published_at,
        "summary_hint": cleaned_summary or _first_sentence(cleaned_content),
        "content": cleaned_content,
        "extraction_sources": list(dict.fromkeys(extraction_sources)),
        "limitations": _dedupe_strings(limitations),
        "blocked": blocked,
    }


def fetch_html(url: str, timeout_seconds: int = 12) -> tuple[str, list[str]]:
    if not _is_fetchable_url(url):
        return "", ["Source fetch warning: invalid or unsupported article URL."]

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace"), []
    except (HTTPError, URLError, TimeoutError) as exc:
        return "", [f"Source fetch warning: {exc}"]


def clean_article_text(text: str) -> str:
    raw = html.unescape(text or "")
    raw = HTML_COMMENT_PATTERN.sub(" ", raw)
    raw = SCRIPT_PATTERN.sub(" ", raw)

    if "<" in raw and ">" in raw:
        if BeautifulSoup is not None:
            soup = BeautifulSoup(raw, "html.parser")
            for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
                tag.decompose()
            if Comment is not None:
                for comment in soup.find_all(string=lambda value: isinstance(value, Comment)):
                    comment.extract()
            raw = soup.get_text("\n")
        else:
            raw = TAG_PATTERN.sub(" ", raw)

    lines: list[str] = []
    seen: set[str] = set()

    for line in raw.splitlines():
        compact = _strip_list_markers(WHITESPACE_PATTERN.sub(" ", line))
        if len(compact) < 2:
            continue

        lowered = compact.lower()
        if any(pattern in lowered for pattern in BOILERPLATE_PATTERNS):
            continue

        normalized = lowered.strip()
        if normalized in seen:
            continue

        seen.add(normalized)
        lines.append(compact)

    return "\n\n".join(lines).strip()


def _extract_structured_data(html_text: str) -> dict[str, Any]:
    if not html_text:
        return {}

    if BeautifulSoup is None:
        return {}

    soup = BeautifulSoup(html_text, "html.parser")
    article_nodes: list[dict[str, Any]] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw_content = script.string or script.get_text(" ", strip=True)
        if not raw_content.strip():
            continue

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            continue

        _collect_article_nodes(parsed, article_nodes)

    if not article_nodes:
        return {}

    article_node = max(article_nodes, key=lambda item: len(str(item.get("articleBody") or "")))
    author = article_node.get("author")
    publisher = article_node.get("publisher")

    return {
        "title": _normalize_json_ld_text(article_node.get("headline") or article_node.get("name")),
        "description": _normalize_json_ld_text(article_node.get("description")),
        "content": _normalize_json_ld_text(article_node.get("articleBody")),
        "source_name": _extract_json_ld_name(publisher),
        "published_at": article_node.get("datePublished") or article_node.get("dateCreated"),
        "author": _extract_json_ld_name(author),
    }


def _extract_meta_data(html_text: str) -> dict[str, str]:
    if not html_text:
        return {}

    if BeautifulSoup is not None:
        soup = BeautifulSoup(html_text, "html.parser")
        meta_values: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = (tag.get("property") or tag.get("name") or "").lower()
            value = (tag.get("content") or "").strip()
            if key and value:
                meta_values[key] = value

        title_tag = soup.find("title")
        return {
            "title": meta_values.get("og:title") or meta_values.get("twitter:title") or (title_tag.get_text(strip=True) if title_tag else ""),
            "description": meta_values.get("description") or meta_values.get("og:description") or meta_values.get("twitter:description") or "",
            "site_name": meta_values.get("og:site_name") or meta_values.get("application-name") or "",
            "published_at": meta_values.get("article:published_time") or meta_values.get("og:updated_time") or "",
        }

    meta_values = {match.group("key").lower(): match.group("value").strip() for match in META_PATTERN.finditer(html_text)}
    title_match = TITLE_PATTERN.search(html_text)
    return {
        "title": meta_values.get("og:title") or meta_values.get("twitter:title") or (title_match.group(1).strip() if title_match else ""),
        "description": meta_values.get("description") or meta_values.get("og:description") or meta_values.get("twitter:description") or "",
        "site_name": meta_values.get("og:site_name") or meta_values.get("application-name") or "",
        "published_at": meta_values.get("article:published_time") or meta_values.get("og:updated_time") or "",
    }


def _extract_article_paragraphs(html_text: str) -> str:
    if not html_text:
        return ""

    if BeautifulSoup is None:
        paragraph_matches = re.findall(r"<p[^>]*>(.*?)</p>", html_text, flags=re.IGNORECASE | re.DOTALL)
        cleaned = [clean_article_text(match) for match in paragraph_matches]
        filtered = [line for line in cleaned if len(line) > 70]
        return "\n\n".join(filtered)

    soup = BeautifulSoup(html_text, "html.parser")
    containers = [soup.find("article"), soup.find("main"), soup.body]

    for container in containers:
        if container is None:
            continue

        paragraphs = [
            clean_article_text(paragraph.get_text(" ", strip=True))
            for paragraph in container.find_all("p")
        ]
        filtered = [item for item in paragraphs if len(item) > 70]
        if filtered:
            return "\n\n".join(_dedupe_strings(filtered))

    return ""


def _pick_first(values: tuple[Any, ...], sources: list[str], labels: tuple[str, ...]) -> str:
    for index, value in enumerate(values):
        candidate = clean_article_text(str(value or ""))
        if candidate:
            sources.append(labels[index])
            return candidate
    return ""


def _collect_article_nodes(node: Any, bucket: list[dict[str, Any]]) -> None:
    if isinstance(node, dict):
        node_type = node.get("@type")
        if isinstance(node_type, list):
            is_article = any("article" in str(item).lower() for item in node_type)
        else:
            is_article = "article" in str(node_type or "").lower()

        if is_article:
            bucket.append(node)

        for value in node.values():
            _collect_article_nodes(value, bucket)
    elif isinstance(node, list):
        for item in node:
            _collect_article_nodes(item, bucket)


def _extract_json_ld_name(node: Any) -> str:
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return str(node.get("name") or "").strip()
    if isinstance(node, list):
        names = [_extract_json_ld_name(item) for item in node]
        return ", ".join(item for item in names if item)
    return ""


def _normalize_json_ld_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n\n".join(str(item).strip() for item in value if str(item).strip())
    return ""


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text or "", maxsplit=1)
    return parts[0].strip() if parts else ""


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(item.strip())
    return result
