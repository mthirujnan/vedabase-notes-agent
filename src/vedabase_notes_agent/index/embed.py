"""
embed.py
--------
Converts text into embedding vectors using a local model.

Beginner tip — what is an embedding?
  An embedding is a list of numbers that represents the *meaning* of text.
  Texts with similar meanings get similar numbers.
  This lets us do "semantic search" — find passages about "self-control"
  even if the query uses different words like "restraining the senses".

We use sentence-transformers which runs entirely on your laptop.
No API key needed for embeddings. The model downloads once (~90 MB)
and is cached in ~/.cache/huggingface/.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from vedabase_notes_agent.config import EMBED_MODEL


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Load (and cache) the embedding model.

    @lru_cache means this function only runs once — the model is loaded
    on first call and reused for every subsequent call. Loading a model
    takes a few seconds so we avoid doing it repeatedly.
    """
    return SentenceTransformer(EMBED_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of strings into a list of embedding vectors.

    Each vector is a list of 384 floats (for all-MiniLM-L6-v2).
    ChromaDB stores these vectors and uses them to find similar chunks.
    """
    model = get_model()
    # encode() returns numpy arrays; tolist() converts to plain Python lists
    return model.encode(texts, show_progress_bar=False).tolist()


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string.
    Used at search time to find chunks similar to the query.
    """
    return embed_texts([query])[0]
