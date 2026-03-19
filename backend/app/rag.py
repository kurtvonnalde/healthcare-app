
from typing import List
from app.schemas import ChatMessage
from app.search_client import search_top_k
from app.llm_client import chat_completion
from app.config import settings

SYSTEM_PROMPT = """You are a healthcare assistant for a demo app.
You MUST follow these rules:
1) Only answer using the provided SOURCES.
2) If the sources do not contain enough information, say you don't have enough information.
3) Cite sources using [1], [2], etc. after relevant sentences.
4) Do NOT fabricate patient details or medical advice. Provide informational summaries only.
"""

def _format_sources(items):
    lines = []
    citations = []
    for idx, it in enumerate(items, start=1):
        content = (it.get("content") or "").strip()
        if len(content) > 1200:
            content = content[:1200] + "…"
        lines.append(
            f"[{idx}] title={it.get('title')}\n"
            f"source={it.get('source')}\n"
            f"path={it.get('path')}\n"
            f"content={content}\n"
        )
        citations.append({
            "title": it.get("title"),
            "source": it.get("source"),
            "path": it.get("path"),
            "chunk_id": it.get("chunk_id"),
            "score": it.get("score"),
        })
    return "\n".join(lines), citations

def _has_enough_signal(items, min_score: float):
    # If scores are missing, allow; otherwise require at least one decent score.
    scores = [it.get("score") for it in items if it.get("score") is not None]
    if not scores:
        return True
    return max(scores) >= min_score

async def answer_question(question: str, top_k: int | None = None):
    k = top_k or settings.top_k
    retrieved = search_top_k(question, k)

    if not retrieved:
        return {
            "answer": "I don't have enough information in the indexed data to answer that question.",
            "grounded": False,
            "reason": "No results returned from search.",
            "citations": []
        }

    if not _has_enough_signal(retrieved, settings.min_score):
        return {
            "answer": "I don't have enough information in the indexed data to answer that question.",
            "grounded": False,
            "reason": "Search results did not meet relevance threshold.",
            "citations": []
        }

    sources_block, citations = _format_sources(retrieved)

    user_prompt = f"""QUESTION:
{question}

SOURCES:
{sources_block}

INSTRUCTIONS:
- Use only SOURCES.
- Provide a concise answer.
- Add citations like [1], [2].
- If missing info, say so clearly.
"""

    text = await chat_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=500
    )

    return {
        "answer": text.strip(),
        "grounded": True,
        "reason": None,
        "citations": citations
    }


SYSTEM_PROMPT = """You are a healthcare assistant for a demo app.

RULES:
1) Use ONLY the provided SOURCES for factual claims.
2) If SOURCES don't contain enough info, say: "I don't have enough information based on the provided sources."
3) Cite sources like [1], [2] right after the sentence they support.
4) Do NOT fabricate patient details or medical advice. Provide informational summaries only.
"""

def _history_to_text(messages: List[ChatMessage], max_turns: int = 8) -> str:
    """
    Convert the last N messages into a short transcript.
    We limit turns to avoid token bloat.
    """
    tail = messages[-max_turns:]
    lines = []
    for m in tail:
        role = "User" if m.role == "user" else "Assistant"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)

async def answer_chat(messages: List[ChatMessage], top_k: int | None = None):
    # 1) Find latest user message
    last_user = next((m.content for m in reversed(messages) if m.role == "user"), None)
    if not last_user:
        return {
            "answer": "Please provide a question.",
            "grounded": False,
            "reason": "No user message found.",
            "citations": []
        }

    k = top_k or settings.top_k

    # 2) Use light context to improve retrieval (optional but helpful)
    history_text = _history_to_text(messages, max_turns=8)

    # Retrieval query strategy:
    # - For best relevance, use the last user question.
    # - If follow-ups like "what about the last one?" happen, context helps.
    retrieval_query = f"{last_user}\nContext:\n{history_text}"

    retrieved = search_top_k(retrieval_query, k)

    # 3) If nothing useful retrieved, refuse
    if not retrieved or not any((r.get("content") or "").strip() for r in retrieved):
        return {
            "answer": "I don't have enough information based on the provided sources.",
            "grounded": False,
            "reason": "No usable search results.",
            "citations": []
        }

    # 4) Format sources for the prompt + citations for the UI
    sources_lines = []
    citations = []

    for idx, it in enumerate(retrieved, start=1):
        content = (it.get("content") or "").strip()
        if len(content) > 1200:
            content = content[:1200] + "…"

        sources_lines.append(
            f"[{idx}] title={it.get('title')}\n"
            f"source={it.get('source')}\n"
            f"path={it.get('path')}\n"
            f"content={content}\n"
        )

        citations.append({
            "title": it.get("title"),
            "source": it.get("source"),
            "path": it.get("path"),
            "chunk_id": it.get("chunk_id"),
            "score": it.get("score"),
        })

    sources_block = "\n".join(sources_lines)

    # 5) Build user prompt with conversation + sources
    user_prompt = f"""CONVERSATION (recent):
{history_text}

LATEST QUESTION:
{last_user}

SOURCES:
{sources_block}

INSTRUCTIONS:
- Answer the LATEST QUESTION only.
- Use ONLY SOURCES for factual claims.
- Add citations like [1], [2] after the sentences they support.
- If insufficient, say you don't have enough information based on the provided sources.
"""

    # 6) Call Azure OpenAI
    answer_text = await chat_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=650
    )

    return {
        "answer": answer_text.strip(),
        "grounded": True,
        "reason": None,
        "citations": citations
    }
