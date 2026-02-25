"""
test_chunk.py — Tests for the text chunker.
Run with: python -m pytest tests/
"""

from vedabase_notes_agent.chunk.chunk_text import _chunk_record

SAMPLE_RECORD = {
    "id":             "NOI-1",
    "book":           "NOI",
    "verse_number":   "1",
    "verse_sanskrit": "vāco vegaṁ manasaḥ",
    "translation":    "A sober person who can tolerate the urge to speak...",
    "purport":        "Gosvāmī means master of the senses. " * 50,  # long purport
    "section_title":  "Text 1",
    "source_uri":     "https://vedabase.io/en/library/noi/1/",
}

SAMPLE_SHORT_RECORD = {
    **SAMPLE_RECORD,
    "verse_number": "9",
    "id":           "NOI-9",
    "purport":      "Short purport for testing.",
}

SAMPLE_PREFACE = {
    "id":             "NOI-preface",
    "book":           "NOI",
    "verse_number":   "preface",
    "verse_sanskrit": "",
    "translation":    "",
    "purport":        "Paragraph one.\n\nParagraph two.\n\nParagraph three.",
    "section_title":  "Preface",
    "source_uri":     "https://vedabase.io/en/library/noi/preface/",
}


def test_chunk_produces_output():
    chunks = _chunk_record(SAMPLE_RECORD)
    assert len(chunks) >= 1


def test_chunk_ids_are_unique():
    chunks = _chunk_record(SAMPLE_RECORD)
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs are not unique"


def test_chunk_has_required_fields():
    chunks = _chunk_record(SAMPLE_RECORD)
    for chunk in chunks:
        for field in ["chunk_id", "parent_id", "book", "verse_number", "text", "source_uri"]:
            assert field in chunk, f"Chunk missing field: {field}"


def test_chunk_verse_number_preserved():
    chunks = _chunk_record(SAMPLE_RECORD)
    for chunk in chunks:
        assert chunk["verse_number"] == "1"


def test_long_purport_split_into_multiple():
    chunks = _chunk_record(SAMPLE_RECORD)
    purport_chunks = [c for c in chunks if "purport" in c["section"]]
    assert len(purport_chunks) >= 2, "Long purport should produce 2 purport chunks"


def test_short_purport_stays_one_chunk():
    chunks = _chunk_record(SAMPLE_SHORT_RECORD)
    purport_chunks = [c for c in chunks if "purport" in c["section"]]
    assert len(purport_chunks) == 1, "Short purport should stay as one chunk"


def test_preface_chunked_by_paragraph():
    chunks = _chunk_record(SAMPLE_PREFACE)
    assert len(chunks) >= 2, "Preface should produce multiple paragraph chunks"


def test_no_empty_chunks():
    chunks = _chunk_record(SAMPLE_RECORD)
    for chunk in chunks:
        assert len(chunk["text"].strip()) > 10, "Chunk text should not be empty"
