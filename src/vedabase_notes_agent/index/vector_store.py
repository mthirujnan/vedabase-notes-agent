"""
vector_store.py
---------------
Manages the local ChromaDB vector database.

Beginner tip — what is a vector database?
  A normal database stores text and lets you search by exact words.
  A vector database stores numbers (embeddings) and lets you search
  by *meaning*. You ask "find passages about sense control" and it
  finds the most semantically similar chunks even if they use
  different words.

ChromaDB stores everything in a local folder (data/index/).
No server to start, no cloud account needed. Just files on disk.
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings

from vedabase_notes_agent.config import INDEX_DIR
from vedabase_notes_agent.index.embed import embed_texts

# Name for our collection inside ChromaDB (like a table in a SQL database)
COLLECTION_NAME = "noi"


def get_client() -> chromadb.PersistentClient:
    """
    Open (or create) the local ChromaDB database.
    Data is saved to data/index/ so it persists between sessions.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(INDEX_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(client: chromadb.PersistentClient | None = None):
    """
    Get the NOI collection, creating it if it doesn't exist.
    """
    client = client or get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        # ChromaDB will use our embeddings, not its own
        metadata={"hnsw:space": "cosine"},
    )


def index_chunks(chunks: list[dict]) -> None:
    """
    Embed all chunks and add them to ChromaDB.

    ChromaDB needs three things per item:
      - ids:        unique string IDs
      - embeddings: the vector for each chunk
      - documents:  the raw text (stored for retrieval)
      - metadatas:  extra info (verse number, source URI, etc.)
    """
    collection = get_collection()

    # Check how many are already indexed to avoid duplicates
    existing = collection.count()
    if existing > 0:
        print(f"  Collection already has {existing} chunks. Clearing and re-indexing...")
        collection.delete(where={"book": "NOI"})

    # Batch processing — embed 32 chunks at a time to avoid memory issues
    batch_size = 32
    total = len(chunks)

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]

        ids        = [c["chunk_id"] for c in batch]
        texts      = [c["text"]     for c in batch]
        metadatas  = [
            {
                "parent_id":    c["parent_id"],
                "book":         c["book"],
                "verse_number": c["verse_number"],
                "section":      c["section"],
                "source_uri":   c["source_uri"],
            }
            for c in batch
        ]

        # Compute embeddings for this batch
        embeddings = embed_texts(texts)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        print(f"  Indexed {min(i + batch_size, total)}/{total} chunks...")


def query_collection(
    query_embedding: list[float],
    top_k: int = 8,
    where: dict | None = None,
) -> list[dict]:
    """
    Search the vector DB for the most similar chunks.

    Returns a list of result dicts, each containing:
      text, chunk_id, verse_number, section, source_uri, distance
    """
    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Flatten ChromaDB's nested result format into a simple list
    hits = []
    for i, doc in enumerate(results["documents"][0]):
        hits.append({
            "text":         doc,
            "chunk_id":     results["ids"][0][i],
            "verse_number": results["metadatas"][0][i]["verse_number"],
            "section":      results["metadatas"][0][i]["section"],
            "source_uri":   results["metadatas"][0][i]["source_uri"],
            "distance":     results["distances"][0][i],
        })

    return hits


def collection_size() -> int:
    """Return the number of chunks currently indexed."""
    return get_collection().count()
