"""
retriever.py
------------
High-level interface for finding relevant NOI chunks for a given query.

Beginner tip — what is RAG?
  RAG = Retrieval Augmented Generation.

  The problem: Claude (the LLM) doesn't have the book memorised perfectly.
  The solution: Before asking Claude to write notes, we *retrieve* the most
  relevant passages from our local vector database and paste them into the
  prompt. Claude then writes notes grounded in those actual passages.

  Flow:
    1. User asks: "notes on controlling the tongue"
    2. Retriever embeds the query → searches ChromaDB → returns top 8 chunks
    3. Agent pastes those chunks into Claude's prompt
    4. Claude writes notes citing [NOI 2 Translation], [NOI 8 Purport], etc.
"""

from vedabase_notes_agent.config import TOP_K
from vedabase_notes_agent.index.embed import embed_query
from vedabase_notes_agent.index.vector_store import query_collection


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Find the top-k most relevant chunks for a given query.

    Args:
        query:  The user's topic or question (plain English)
        top_k:  How many chunks to return (default from config)

    Returns:
        List of chunk dicts, ordered by relevance (most relevant first).
        Each dict has: text, chunk_id, verse_number, section, source_uri, distance
    """
    # Step 1: Convert query to an embedding vector
    query_vec = embed_query(query)

    # Step 2: Search ChromaDB for similar vectors
    hits = query_collection(query_vec, top_k=top_k)

    return hits


def format_context(hits: list[dict], max_chars_per_chunk: int = 600) -> str:
    """
    Format retrieved chunks into a readable context block for Claude's prompt.

    Example output:
      [NOI 1 - translation]
      Source: https://vedabase.io/en/library/noi/1/
      A sober person who can tolerate the urge to speak...

      [NOI 3 - purport]
      Source: https://vedabase.io/en/library/noi/3/
      There are six kinds of aggressors...
    """
    parts = []
    for hit in hits:
        verse = hit["verse_number"]
        section = hit["section"]
        uri = hit["source_uri"]
        text = hit["text"][:max_chars_per_chunk]
        if len(hit["text"]) > max_chars_per_chunk:
            text += "..."

        # Format the citation label clearly so Claude can reference it
        label = f"NOI {verse}".upper() if verse != "preface" else "NOI Preface"
        parts.append(
            f"[{label} - {section}]\n"
            f"Source: {uri}\n"
            f"{text}"
        )

    return "\n\n---\n\n".join(parts)


def citation_label(hit: dict) -> str:
    """
    Return the short citation string for a chunk, e.g. '[NOI 3 Purport]'.
    Used in notes and verification.
    """
    verse   = hit["verse_number"].capitalize()
    section = hit["section"].capitalize()
    return f"[NOI {verse} {section}]"
