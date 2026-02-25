"""
parse_noi.py
------------
Converts raw scraped pages → structured JSONL records.

Each output record follows this schema:
  {
    "id":             "NOI-1",          # unique ID
    "book":           "NOI",
    "verse_number":   "1",              # "preface" for the preface
    "verse_sanskrit": "vāco vegaṁ ...", # transliteration line (may be empty)
    "translation":    "A sober person ...",
    "purport":        "In the Bhagavad-gita ...",
    "section_title":  "Text 1",
    "source_uri":     "https://vedabase.io/en/library/noi/1/"
  }

Beginner tip — what is JSONL?
  JSONL = "JSON Lines". Each line of the file is one JSON object.
  It's great for large datasets because you can read one line at a time
  without loading the whole file into memory.
"""

import json
import re
from pathlib import Path

from rich.console import Console

from vedabase_notes_agent.config import CLEAN_DIR, RAW_DIR

console = Console()


# ── Public entry point ────────────────────────────────────────────────────────

def parse_noi(
    raw_file: Path | None = None,
    out_file: Path | None = None,
) -> Path:
    """
    Read the raw JSON, parse each page, and write clean JSONL.

    Returns the path to the output .jsonl file.
    """
    raw_file = raw_file or (RAW_DIR / "noi" / "noi_raw.json")
    out_file = out_file or (CLEAN_DIR / "noi_clean.jsonl")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Load raw pages
    with open(raw_file, encoding="utf-8") as f:
        pages: list[dict] = json.load(f)

    console.print(f"[cyan]Parsing {len(pages)} pages...[/]")

    records: list[dict] = []
    for page in pages:
        record = _parse_page(page)
        if record:
            records.append(record)

    # Write one JSON object per line
    with open(out_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    console.print(f"[green]Parsed {len(records)} records →[/] {out_file}")
    return out_file


# ── Per-page parsing ──────────────────────────────────────────────────────────

def _parse_page(page: dict) -> dict | None:
    """
    Parse one raw page dict into a structured record.

    The raw text looks roughly like:
      "... Text 1 Sanskrit transliteration ... TRANSLATION A sober person ...
       PURPORT In the Bhagavad-gita ..."
    """
    raw_text: str = page.get("text", "")
    page_id:  str = page.get("id", "")
    title:    str = page.get("title", "")
    url:      str = page.get("url", "")

    if not raw_text.strip():
        return None

    # Determine verse number ("preface" or "1".."11")
    verse_number = "preface" if page_id == "preface" else page_id

    # Extract sections using keyword boundaries
    translation = _extract_section(raw_text, start_kw="TRANSLATION", end_kw="PURPORT")
    purport      = _extract_section(raw_text, start_kw="PURPORT",     end_kw=None)
    sanskrit     = _extract_transliteration(raw_text)

    # For preface there is no verse/translation structure — use full text
    if verse_number == "preface":
        translation = ""
        purport      = raw_text.strip()[:3000]  # keep reasonable length
        sanskrit     = ""

    return {
        "id":             f"NOI-{verse_number}",
        "book":           "NOI",
        "verse_number":   verse_number,
        "verse_sanskrit": sanskrit,
        "translation":    translation.strip(),
        "purport":        purport.strip(),
        "section_title":  title,
        "source_uri":     url,
    }


# ── Section extraction helpers ────────────────────────────────────────────────

def _extract_section(text: str, start_kw: str, end_kw: str | None) -> str:
    """
    Extract the text between two keyword markers (case-insensitive).

    Example:
      text = "...TRANSLATION A sober person...PURPORT In the..."
      _extract_section(text, "TRANSLATION", "PURPORT")
      → "A sober person..."
    """
    # Build a regex that finds everything after start_kw up to end_kw (or end of string)
    if end_kw:
        pattern = rf"{start_kw}\s*(.*?)\s*{end_kw}"
    else:
        pattern = rf"{start_kw}\s*(.*)"

    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _extract_transliteration(text: str) -> str:
    """
    Try to find the Roman transliteration line (e.g. "vāco vegaṁ manasaḥ...").

    The transliteration typically:
      - Appears before the word-for-word section
      - Contains characteristic diacritic characters (ā, ī, ū, ṛ, ṁ, ḥ, etc.)
      - Is on its own line or separated by newlines
    """
    # Look for lines containing Sanskrit diacritic characters
    diacritic_pattern = r"[āīūṛṝḷṭḍṇśṣñṁḥĀĪŪ]"

    for line in text.split("\n"):
        line = line.strip()
        # A transliteration line: has diacritics, is reasonably long, not a heading
        if (
            re.search(diacritic_pattern, line)
            and len(line) > 20
            and len(line) < 500
            and "TRANSLATION" not in line.upper()
            and "PURPORT" not in line.upper()
        ):
            return line

    return ""


# ── Utility: load clean records ───────────────────────────────────────────────

def load_clean_records(clean_file: Path | None = None) -> list[dict]:
    """
    Read the clean JSONL file and return a list of record dicts.
    Used by downstream stages (chunk, index, etc.).
    """
    clean_file = clean_file or (CLEAN_DIR / "noi_clean.jsonl")
    records = []
    with open(clean_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
