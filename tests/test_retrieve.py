"""
test_retrieve.py — Tests for the retriever and formatting utilities.
Run with: python -m pytest tests/
"""

from vedabase_notes_agent.retrieve.retriever import format_context, citation_label


SAMPLE_HITS = [
    {
        "text":         "A sober person can tolerate the urge to speak.",
        "chunk_id":     "NOI-1-translation",
        "verse_number": "1",
        "section":      "translation",
        "source_uri":   "https://vedabase.io/en/library/noi/1/",
        "distance":     0.12,
    },
    {
        "text":         "Gosvāmī means master of the senses.",
        "chunk_id":     "NOI-1-purport",
        "verse_number": "1",
        "section":      "purport",
        "source_uri":   "https://vedabase.io/en/library/noi/1/",
        "distance":     0.25,
    },
]


def test_format_context_returns_string():
    result = format_context(SAMPLE_HITS)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_context_includes_labels():
    result = format_context(SAMPLE_HITS)
    assert "NOI" in result
    assert "translation" in result.lower()


def test_format_context_includes_source_uri():
    result = format_context(SAMPLE_HITS)
    assert "vedabase.io" in result


def test_format_context_truncates_long_text():
    long_hit = {**SAMPLE_HITS[0], "text": "x" * 2000}
    result = format_context([long_hit], max_chars_per_chunk=600)
    assert "..." in result


def test_citation_label_verse():
    label = citation_label(SAMPLE_HITS[0])
    assert "NOI" in label
    assert "1" in label
    assert "Translation" in label


def test_citation_label_preface():
    preface_hit = {**SAMPLE_HITS[0], "verse_number": "preface", "section": "preface"}
    label = citation_label(preface_hit)
    assert "Preface" in label


def test_format_context_empty_list():
    result = format_context([])
    assert result == ""
