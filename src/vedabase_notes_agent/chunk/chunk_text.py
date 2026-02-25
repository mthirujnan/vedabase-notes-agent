"""
chunk_text.py
-------------
Splits clean NOI records into chunks suitable for embedding and retrieval.

Beginner tip — why chunk?
  Language models and vector databases work best with small pieces of text
  (~200-500 words). A full purport can be 1000+ words, so we split it into
  overlapping chunks. Each chunk remembers which verse it came from so we
  can always cite the source.

Chunking strategy for NOI:
  Each verse produces up to 3 chunks:
    1. Sanskrit + Translation  (short, focused on the verse itself)
    2. Purport part 1          (first half of the commentary)
    3. Purport part 2          (second half, with overlap from part 1)

  The preface is split by paragraphs.

Output schema per chunk:
  {
    "chunk_id":    "NOI-1-translation",
    "parent_id":   "NOI-1",
    "book":        "NOI",
    "verse_number": "1",
    "section":     "translation" | "purport" | "preface",
    "text":        "A sober person who...",
    "source_uri":  "https://..."
  }
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from vedabase_notes_agent.config import CHUNKS_DIR, CLEAN_DIR

console = Console()

# How many characters before splitting a purport into two chunks
PURPORT_SPLIT_CHARS = 1200
# How many characters of overlap between purport chunks (keeps context)
OVERLAP_CHARS = 200


def chunk_noi(
    clean_file: Path | None = None,
    out_file:   Path | None = None,
) -> Path:
    """
    Read clean JSONL records and write chunk JSONL.
    Returns the path to the chunks file.
    """
    clean_file = clean_file or (CLEAN_DIR / "noi_clean.jsonl")
    out_file   = out_file   or (CHUNKS_DIR / "noi_chunks.jsonl")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Load clean records
    records: list[dict] = []
    with open(clean_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    console.print(f"[cyan]Chunking {len(records)} records...[/]")

    all_chunks: list[dict] = []
    for record in records:
        chunks = _chunk_record(record)
        all_chunks.extend(chunks)

    # Write chunks
    with open(out_file, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    console.print(f"[green]Created {len(all_chunks)} chunks →[/] {out_file}")
    return out_file


def _chunk_record(record: dict) -> list[dict]:
    """
    Split one clean record into 1-3 chunks depending on content length.
    """
    chunks: list[dict] = []
    verse  = record["verse_number"]
    parent = record["id"]
    book   = record["book"]
    uri    = record["source_uri"]

    def make_chunk(section: str, text: str, part: int = 0) -> dict:
        suffix = f"-{part}" if part > 0 else ""
        return {
            "chunk_id":    f"{parent}-{section}{suffix}",
            "parent_id":   parent,
            "book":        book,
            "verse_number": verse,
            "section":     section,
            "text":        text.strip(),
            "source_uri":  uri,
        }

    # ── Preface: split by paragraph ───────────────────────────────────────────
    if verse == "preface":
        paragraphs = [p.strip() for p in record["purport"].split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs, 1):
            if len(para) > 50:  # skip very short fragments
                chunks.append(make_chunk("preface", para, i))
        return chunks

    # ── Translation chunk ─────────────────────────────────────────────────────
    translation_text = ""
    if record.get("verse_sanskrit"):
        translation_text += f"Transliteration: {record['verse_sanskrit']}\n\n"
    if record.get("translation"):
        translation_text += f"Translation: {record['translation']}"

    if translation_text.strip():
        chunks.append(make_chunk("translation", translation_text))

    # ── Purport chunk(s) ──────────────────────────────────────────────────────
    purport = record.get("purport", "").strip()
    if not purport:
        return chunks

    if len(purport) <= PURPORT_SPLIT_CHARS:
        # Short enough to keep as one chunk
        chunks.append(make_chunk("purport", purport))
    else:
        # Split into two overlapping chunks
        mid = len(purport) // 2
        part1 = purport[: mid + OVERLAP_CHARS]
        part2 = purport[mid - OVERLAP_CHARS :]
        chunks.append(make_chunk("purport", part1, part=1))
        chunks.append(make_chunk("purport", part2, part=2))

    return chunks


def load_chunks(chunks_file: Path | None = None) -> list[dict]:
    """
    Utility: load all chunks from JSONL. Used by the indexer.
    """
    chunks_file = chunks_file or (CHUNKS_DIR / "noi_chunks.jsonl")
    chunks = []
    with open(chunks_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks
