"""
export_markdown.py
------------------
Saves generated notes as a Markdown (.md) file.

Markdown is a simple text format that renders nicely in:
  - GitHub (automatically displayed)
  - Obsidian, Notion, or any note-taking app
  - Your browser with a markdown viewer extension
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from vedabase_notes_agent.config import OUT_DIR


def export_notes(notes: str, topic: str, out_dir: Path | None = None) -> Path:
    """
    Save notes to a timestamped markdown file.

    Returns the path to the saved file.

    Filename format: notes_<slug>_<YYYY-MM-DD>.md
    Example: notes_controlling_the_senses_2025-01-01.md
    """
    out_dir = out_dir or OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # Convert topic to a safe filename slug
    # "Controlling the Senses!" → "controlling_the_senses"
    slug = re.sub(r"[^\w\s-]", "", topic.lower())
    slug = re.sub(r"[\s-]+", "_", slug).strip("_")
    slug = slug[:50]  # keep filenames short

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"notes_{slug}_{date_str}.md"
    out_path = out_dir / filename

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(notes)

    return out_path
