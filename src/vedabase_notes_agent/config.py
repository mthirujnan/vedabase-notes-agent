"""
config.py
---------
Central configuration for the entire pipeline.

All file paths, API keys, and model names live here.
Other modules import from this file — nothing is hardcoded elsewhere.

Beginner tip:
  os.getenv("KEY", "default") reads a value from your .env file.
  If the key is missing it returns the default value.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load values from the .env file in the project root
load_dotenv()

# ── Project root and data directories ────────────────────────────────────────
# __file__ is this file: src/vedabase_notes_agent/config.py
# .parent.parent.parent climbs up to the project root
BASE_DIR   = Path(__file__).parent.parent.parent
DATA_DIR   = BASE_DIR / "data"
RAW_DIR    = DATA_DIR / "raw"
CLEAN_DIR  = DATA_DIR / "clean"
CHUNKS_DIR = DATA_DIR / "chunks"
INDEX_DIR  = DATA_DIR / "index"
OUT_DIR    = DATA_DIR / "outputs"

# ── LLM settings ─────────────────────────────────────────────────────────────
CLAUDE_API_KEY : str = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL   : str = os.getenv("CLAUDE_MODEL",   "claude-sonnet-4-6")

# ── Embedding model (runs locally) ───────────────────────────────────────────
# all-MiniLM-L6-v2 is small (~90 MB) and fast — good for a laptop
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# ── Scraper integration ───────────────────────────────────────────────────────
# Path to the existing scraper.py in your noi-search project.
# If set, the ingest step can run the scraper automatically.
# If not set, ingest will look for an existing data.json instead.
NOI_SCRAPER_PATH: Path | None = (
    Path(os.getenv("NOI_SCRAPER_PATH", "")) or None
)

# ── Retrieval settings ────────────────────────────────────────────────────────
# How many chunks to retrieve for each query
TOP_K: int = 8

# ── Agent settings ────────────────────────────────────────────────────────────
MAX_TOKENS: int = 8192   # max tokens Claude can return per call
EXCERPT_MAX_CHARS: int = 300  # max length of quoted excerpts in notes
