"""
ingest_noi.py
-------------
WRAPPER around the existing noi-search scraper.

Design principle:
  We do NOT rewrite scraping logic here.
  The noi-search project already has a working scraper at:
    <your-project>/noi-search/scraper.py

  This module is a thin adapter that:
    1. Tries to import and call the existing scraper
    2. Falls back to reading data.json if scraper isn't available
    3. Saves the result to our data/raw/noi/ directory

Beginner tip — what is a "wrapper"?
  A wrapper is code that calls someone else's code.
  Think of it like a remote control: you press one button and
  it sends the right signal to the TV. You don't need to know
  how the TV works internally.
"""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

from rich.console import Console

from vedabase_notes_agent.config import NOI_SCRAPER_PATH, RAW_DIR

console = Console()


def ingest_noi(out_dir: Path | None = None) -> Path:
    """
    Main entry point for ingestion.

    Returns the Path to the saved raw JSON file.

    Strategy (tries each in order):
      1. If NOI_SCRAPER_PATH is set → import and run the existing scraper
      2. If data.json lives next to the scraper → copy it
      3. Raise a clear error telling the user what to do
    """
    # Where to save the raw output
    out_dir = out_dir or (RAW_DIR / "noi")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "noi_raw.json"

    # ── Strategy 1: Run the existing scraper ─────────────────────────────────
    scraper_path = NOI_SCRAPER_PATH
    if scraper_path and Path(scraper_path).exists():
        console.print(f"[green]Found existing scraper at:[/] {scraper_path}")
        console.print("[yellow]Running scraper (this fetches from vedabase.io)...[/]")

        pages = _run_existing_scraper(Path(scraper_path))
        if pages:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(pages, f, ensure_ascii=False, indent=2)
            console.print(f"[green]Saved {len(pages)} pages →[/] {out_file}")
            return out_file

    # ── Strategy 2: Look for data.json next to the scraper ───────────────────
    if scraper_path:
        data_json = Path(scraper_path).parent / "data.json"
        if data_json.exists():
            console.print(f"[green]Found existing data.json at:[/] {data_json}")
            shutil.copy(data_json, out_file)
            console.print(f"[green]Copied to →[/] {out_file}")
            return out_file

    # ── Strategy 3: Look for data.json in the default noi-search location ────
    # Check common sibling directory location
    default_data = (
        Path(__file__).parent.parent.parent.parent.parent
        / "noi-search" / "data.json"
    )
    if default_data.exists():
        console.print(f"[green]Found data.json at:[/] {default_data}")
        shutil.copy(default_data, out_file)
        console.print(f"[green]Copied to →[/] {out_file}")
        return out_file

    # ── Nothing found — give clear instructions ───────────────────────────────
    raise FileNotFoundError(
        "\n\n[bold red]Cannot find scraped data.[/]\n\n"
        "Please do ONE of the following:\n\n"
        "  Option A — Set NOI_SCRAPER_PATH in your .env file:\n"
        "    NOI_SCRAPER_PATH=/path/to/noi-search/scraper.py\n\n"
        "  Option B — Manually copy data.json:\n"
        "    cp /path/to/noi-search/data.json data/raw/noi/noi_raw.json\n\n"
        "  Option C — Run the noi-search scraper manually:\n"
        "    cd /path/to/noi-search && python3 scraper.py\n"
        "    Then set NOI_SCRAPER_PATH and run ingest again.\n"
    )


def _run_existing_scraper(scraper_path: Path) -> list[dict] | None:
    """
    Dynamically import the existing scraper module and call its scrape() function.

    importlib lets us load a Python file by path at runtime —
    like doing 'import scraper' but from any location on disk.

    The existing scraper writes to data.json on disk AND we intercept
    the result by reading the file it creates.
    """
    try:
        # Load the scraper module from disk
        spec = importlib.util.spec_from_file_location("noi_scraper", scraper_path)
        if spec is None or spec.loader is None:
            console.print("[red]Could not load scraper module.[/]")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules["noi_scraper"] = module

        # Change working directory so scraper writes files in its own folder
        import os
        original_cwd = os.getcwd()
        os.chdir(scraper_path.parent)

        spec.loader.exec_module(module)  # type: ignore

        # Call the scraper's scrape() function
        module.scrape()  # type: ignore

        # The scraper writes data.json — read it back
        data_json = scraper_path.parent / "data.json"
        if data_json.exists():
            with open(data_json, encoding="utf-8") as f:
                pages = json.load(f)
            os.chdir(original_cwd)
            return pages

        os.chdir(original_cwd)
        return None

    except Exception as exc:
        console.print(f"[red]Scraper error:[/] {exc}")
        console.print("[yellow]Falling back to data.json copy...[/]")
        return None
