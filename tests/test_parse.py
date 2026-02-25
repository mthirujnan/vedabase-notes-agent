"""
test_parse.py — Tests for the NOI parser.
Run with: python -m pytest tests/
"""

import pytest
from vedabase_notes_agent.parse.parse_noi import _parse_page, _extract_section


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_RAW_PAGE = {
    "id":    "1",
    "title": "Text 1",
    "url":   "https://vedabase.io/en/library/noi/1/",
    "text": (
        "Nectar of Instruction Text 1 "
        "vāco vegaṁ manasaḥ krodha-vegaṁ jihvā-vegam udaropastha-vegam "
        "TRANSLATION "
        "A sober person who can tolerate the urge to speak, the mind's demands, "
        "the actions of anger and the urges of the tongue, belly and genitals is "
        "qualified to make disciples all over the world. "
        "PURPORT "
        "Gosvāmī means master of the senses and the mind. "
        "The six Gosvāmīs of Vṛndāvana were great personalities. "
        "One who controls the tongue, belly, and genitals is a gosvāmī."
    ),
    "translation": "A sober person...",
}

SAMPLE_PREFACE_PAGE = {
    "id":    "preface",
    "title": "Preface",
    "url":   "https://vedabase.io/en/library/noi/preface/",
    "text":  "This is the preface.\n\nIt has multiple paragraphs.\n\nEach discusses important topics.",
    "translation": "",
}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_parse_verse_has_required_fields():
    record = _parse_page(SAMPLE_RAW_PAGE)
    assert record is not None
    for field in ["id", "book", "verse_number", "translation", "purport", "source_uri"]:
        assert field in record, f"Missing field: {field}"


def test_parse_verse_number():
    record = _parse_page(SAMPLE_RAW_PAGE)
    assert record["verse_number"] == "1"


def test_parse_book_name():
    record = _parse_page(SAMPLE_RAW_PAGE)
    assert record["book"] == "NOI"


def test_parse_translation_extracted():
    record = _parse_page(SAMPLE_RAW_PAGE)
    assert "sober person" in record["translation"]


def test_parse_purport_extracted():
    record = _parse_page(SAMPLE_RAW_PAGE)
    assert "Gosvāmī" in record["purport"] or "gosvami" in record["purport"].lower()


def test_parse_preface():
    record = _parse_page(SAMPLE_PREFACE_PAGE)
    assert record is not None
    assert record["verse_number"] == "preface"
    assert len(record["purport"]) > 0


def test_extract_section_basic():
    text = "Some text TRANSLATION This is the translation. PURPORT This is the purport."
    result = _extract_section(text, "TRANSLATION", "PURPORT")
    assert "This is the translation" in result


def test_extract_section_to_end():
    text = "PURPORT This is the purport text until the end of the string."
    result = _extract_section(text, "PURPORT", None)
    assert "purport text" in result


def test_empty_page_returns_none():
    result = _parse_page({"id": "1", "title": "T", "url": "http://x.com", "text": ""})
    assert result is None
