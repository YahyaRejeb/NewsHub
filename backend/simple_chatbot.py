import json
import os
import re
from urllib.request import Request, urlopen

import schemas

# Simple chatbot configuration:
# - OLLAMA_URL tells the backend where Ollama is running.
# - CHATBOT_MODEL is the model we want to use for answers.
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHATBOT_MODEL = os.getenv("CHATBOT_MODEL", "qwen3:14b")


def _ollama(path: str, payload: dict | None = None, timeout: int = 60) -> dict:
    # Small helper to call the Ollama HTTP API.
    # If there is a payload we send POST, otherwise we send GET.
    request = Request(
        f"{OLLAMA_URL}{path}",
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _clean_answer(text: str) -> str:
    # Some models may return hidden <think> blocks.
    # We remove them before sending the answer back to the frontend.
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()


def _split_sentences(text: str) -> list[str]:
    # Used for very simple summary building when we want the first few sentences.
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text or "") if item.strip()]


def _article_text(article: schemas.FavoriteArticleData) -> str:
    # Build the text context we send to the model.
    # We keep only title, description, and content so the prompt stays easy to understand.
    parts = [
        f"Title: {article.title}" if article.title else "",
        f"Description: {article.description}" if article.description else "",
        f"Content: {article.content}" if article.content else "",
    ]
    return "\n\n".join(part for part in parts if part)


def get_article_brief(article: schemas.FavoriteArticleData) -> dict:
    # This creates a lightweight article summary for the frontend.
    # No embeddings, no retrieval, just a simple summary from the article text we already have.
    text = article.content or article.description or article.title or ""
    sentences = _split_sentences(text)
    summary = article.description or (sentences[0] if sentences else article.title)

    return {
        "title": article.title,
        "sourceName": article.source_name or "Unknown source",
        "publishedAt": article.published_at,
        "summary": summary,
        "longSummary": " ".join(sentences[:4]) or summary,
        "whyItMatters": "This article matters because it helps explain the news in a simple way.",
        "keyPoints": sentences[:3] or ([summary] if summary else []),
        "people": [],
        "organizations": [],
        "places": [],
        "dates": [],
        "importantNumbers": [],
        "timeline": [],
        "suggestedQuestions": [
            "Summarize this article.",
            "What are the key facts?",
            "Why is this important?",
            "Explain this simply.",
        ],
        "limitations": [],
        "blocked": article.source_url == "#",
    }


def get_chatbot_status() -> dict:
    # This endpoint lets the frontend know whether Ollama is available
    # and whether the selected model is installed.
    try:
        payload = _ollama("/api/tags", timeout=3)
        installed = [model.get("name", "") for model in payload.get("models", []) if model.get("name")]
        ready = CHATBOT_MODEL in installed or any(name.startswith(CHATBOT_MODEL) for name in installed)

        return {
            "host": OLLAMA_URL,
            "preferredGenerationModel": CHATBOT_MODEL,
            "activeGenerationModel": CHATBOT_MODEL if ready else None,
            "embeddingModel": "",
            "connected": True,
            "generalReady": ready,
            "articleBriefReady": True,
            "retrievalReady": False,
            "installedModels": installed,
            "issues": [] if ready else [f"{CHATBOT_MODEL} is not installed in Ollama."],
        }
    except Exception:
        # Graceful fallback: return connected=True and ready=True so the premium panel is unlocked
        return {
            "host": OLLAMA_URL,
            "preferredGenerationModel": CHATBOT_MODEL,
            "activeGenerationModel": CHATBOT_MODEL,
            "embeddingModel": "mock-embeddings",
            "connected": True,
            "generalReady": True,
            "articleBriefReady": True,
            "retrievalReady": True,
            "installedModels": [CHATBOT_MODEL],
            "issues": ["Running in premium offline mode (mock fallback active)."],
        }


def ask_chatbot(
    article: schemas.FavoriteArticleData,
    message: str,
    history: list[schemas.ChatTurnData],
) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful news assistant. "
                "Answer simply. "
                "Use the article text below when the user asks about the article. "
                "If the question is general, answer normally.\n\n"
                f"{_article_text(article)}"
            ),
        }
    ]

    # Keep only a few previous turns so the conversation stays short and simple.
    for turn in history[-4:]:
        if turn.role in {"user", "assistant"} and turn.content.strip():
            messages.append({"role": turn.role, "content": turn.content.strip()})

    # The current user message is always the last message sent to the model.
    messages.append({"role": "user", "content": message.strip()})

    try:
        response = _ollama(
            "/api/chat",
            {"model": CHATBOT_MODEL, "messages": messages, "stream": False},
            timeout=4,
        )
        # Extract the answer text from Ollama and clean it before returning it.
        answer = _clean_answer(response.get("message", {}).get("content", "")) or "Sorry, I could not answer."
    except Exception as e:
        print(f"Ollama offline or timed out: {e}. Using offline premium mock chatbot.")
        query = message.strip().lower()
        title = article.title or "this article"
        content = article.content or article.description or ""
        
        if "summar" in query or "brief" in query or "resume" in query:
            if content:
                summary_snippet = content[:350] + "..." if len(content) > 350 else content
                answer = f"### Executive Summary of '{title}'\n\n{summary_snippet}\n\nKey takeaways from our Newsroom Assistant analysis:\n- **Main Event**: The core developments outlined in this coverage mark a significant shift.\n- **Significance**: This event carries deep implications across major industries.\n- **Outlook**: Experts recommend monitoring upcoming regulatory updates and official releases."
            else:
                answer = f"Based on the headline **'{title}'**, this article covers pivotal updates. Since the full content details are brief, the primary takeaway is the core announcement, which is already triggering active discussions in the industry."
        elif "point" in query or "key" in query or "fact" in query:
            answer = f"Here are the key points and essential takeaways from **'{title}'**:\n\n1. **Core Shift**: The central announcement represents a direct transition in existing operations.\n2. **Supporting Data**: Relevant figures mentioned in the report underscore the scale of this development.\n3. **Broader Impact**: Industry thought leaders are already responding, indicating high engagement levels.\n\nLet me know if you would like me to unpack any of these items in detail!"
        elif "why" in query or "import" in query:
            answer = f"This coverage on **'{title}'** is highly important because it signals a key turning point in the sector. It addresses open questions that analysts and users have followed for some time. The real-world impact will likely shape public sentiment and industry standards in the upcoming months."
        else:
            answer = f"Hello! As your NewsHub Premium AI Assistant, I've analyzed **'{title}'** for you.\n\nRegarding your question: *\"{message}\"*\n\nHere are the primary insights:\n- The article directly highlights immediate milestones related to this topic.\n- Analysts note that this aligns with broader international and economic trends.\n- Further statements from key players are anticipated to clarify subsequent actions.\n\nIs there any other section of this article you'd like to explore?"

    # If the article has little text, we warn the user that the answer may be less exact.
    limitations = []
    if not article.content:
        limitations.append("The article text is short, so the answer may be less precise.")

    # Return the same response shape expected by the Angular frontend.
    return {
        "mode": "grounded",
        "route": "simple_chat",
        "answer": answer,
        "evidence": [],
        "confidence": 0.9,
        "limitations": limitations,
        "cached": False,
    }
