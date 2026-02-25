"""
cli.py
------
Command-line interface for the vedabase-notes-agent.

Beginner tip — what is a CLI?
  CLI = Command Line Interface. Instead of clicking buttons,
  you type commands in the Terminal. Each command here runs
  one stage of the pipeline.

Usage examples:
  python -m vedabase_notes_agent.cli ingest-noi
  python -m vedabase_notes_agent.cli parse --book NOI
  python -m vedabase_notes_agent.cli chunk --book NOI
  python -m vedabase_notes_agent.cli index --book NOI
  python -m vedabase_notes_agent.cli generate-notes --topic "controlling the senses"
  python -m vedabase_notes_agent.cli smoke-test
"""

from pathlib import Path

import click
from rich.console import Console

console = Console()

# ── CLI group ─────────────────────────────────────────────────────────────────
# @click.group() means this file is a collection of subcommands,
# like how "git" has "git commit", "git push", etc.

@click.group()
def cli():
    """Vedabase Notes Agent — study notes with citations from Nectar of Instruction."""
    pass


# ── ingest-noi ────────────────────────────────────────────────────────────────

@cli.command("ingest-noi")
@click.option(
    "--out",
    default=None,
    help="Output directory for raw data (default: data/raw/noi/)",
)
def ingest_noi_cmd(out):
    """
    STEP 1: Fetch raw content from vedabase.io using the existing scraper.

    This wraps the scraper from the noi-search project.
    Set NOI_SCRAPER_PATH in your .env file to point to it.
    """
    console.print("\n[bold]Step 1 — Ingest NOI[/]")
    console.print("Reusing existing scraper from noi-search project...\n")

    from vedabase_notes_agent.ingest.ingest_noi import ingest_noi

    out_path = Path(out) if out else None
    result = ingest_noi(out_dir=out_path)
    console.print(f"\n[bold green]Done.[/] Raw data saved to: {result}")


# ── parse ─────────────────────────────────────────────────────────────────────

@cli.command("parse")
@click.option("--book", default="NOI", show_default=True, help="Book to parse.")
@click.option("--raw",  default=None, help="Path to raw JSON file.")
@click.option("--out",  default=None, help="Path for output JSONL file.")
def parse_cmd(book, raw, out):
    """
    STEP 2: Parse raw pages into structured JSONL records.

    Extracts: verse number, Sanskrit, translation, purport, source URI.
    """
    console.print(f"\n[bold]Step 2 — Parse {book}[/]\n")

    if book.upper() != "NOI":
        console.print(f"[red]Unknown book: {book}. Only NOI is supported.[/]")
        raise SystemExit(1)

    from vedabase_notes_agent.parse.parse_noi import parse_noi

    raw_path = Path(raw) if raw else None
    out_path = Path(out) if out else None
    result   = parse_noi(raw_file=raw_path, out_file=out_path)
    console.print(f"\n[bold green]Done.[/] Clean records saved to: {result}")


# ── chunk ─────────────────────────────────────────────────────────────────────

@cli.command("chunk")
@click.option("--book", default="NOI", show_default=True, help="Book to chunk.")
@click.option("--clean", default=None, help="Path to clean JSONL file.")
@click.option("--out",   default=None, help="Path for output chunks JSONL.")
def chunk_cmd(book, clean, out):
    """
    STEP 3: Split clean records into chunks for the vector database.

    Each verse produces 1-3 chunks (translation + purport parts).
    """
    console.print(f"\n[bold]Step 3 — Chunk {book}[/]\n")

    if book.upper() != "NOI":
        console.print(f"[red]Unknown book: {book}.[/]")
        raise SystemExit(1)

    from vedabase_notes_agent.chunk.chunk_text import chunk_noi

    clean_path = Path(clean) if clean else None
    out_path   = Path(out)   if out   else None
    result     = chunk_noi(clean_file=clean_path, out_file=out_path)
    console.print(f"\n[bold green]Done.[/] Chunks saved to: {result}")


# ── index ─────────────────────────────────────────────────────────────────────

@cli.command("index")
@click.option("--book",   default="NOI", show_default=True, help="Book to index.")
@click.option("--chunks", default=None, help="Path to chunks JSONL file.")
def index_cmd(book, chunks):
    """
    STEP 4: Embed chunks and store them in the local vector database (ChromaDB).

    Downloads the embedding model on first run (~90 MB, then cached).
    """
    console.print(f"\n[bold]Step 4 — Index {book}[/]\n")

    if book.upper() != "NOI":
        console.print(f"[red]Unknown book: {book}.[/]")
        raise SystemExit(1)

    from vedabase_notes_agent.chunk.chunk_text import load_chunks
    from vedabase_notes_agent.index.vector_store import index_chunks, collection_size

    chunks_path = Path(chunks) if chunks else None
    all_chunks  = load_chunks(chunks_path)

    console.print(f"Loaded {len(all_chunks)} chunks. Embedding and indexing...")
    index_chunks(all_chunks)
    console.print(f"\n[bold green]Done.[/] {collection_size()} chunks now in vector DB.")


# ── generate-notes ────────────────────────────────────────────────────────────

@cli.command("generate-notes")
@click.option("--book",         default="NOI",              show_default=True)
@click.option("--topic",        required=True,              help="Topic for the notes.")
@click.option("--audience",     default="general devotees", show_default=True)
@click.option("--duration-min", default=60,                 show_default=True, type=int)
@click.option(
    "--style",
    default="class",
    show_default=True,
    type=click.Choice(["class", "discourse"]),
    help="class = structured lecture; discourse = flowing talk",
)
@click.option("--out", default=None, help="Output directory (default: data/outputs/)")
def generate_notes_cmd(book, topic, audience, duration_min, style, out):
    """
    STEP 5: Generate study notes using the AI agent.

    Runs the full agent loop: retrieve → plan → draft → verify → save.

    Example:
      python -m vedabase_notes_agent.cli generate-notes \\
        --topic "controlling the six urges" --duration-min 90
    """
    console.print(f"\n[bold]Generating notes for:[/] {topic}")
    console.print(f"  Audience: {audience}")
    console.print(f"  Duration: {duration_min} min")
    console.print(f"  Style:    {style}\n")

    from vedabase_notes_agent.agent.notes_agent import generate_notes
    from vedabase_notes_agent.export.export_markdown import export_notes

    notes    = generate_notes(topic, audience, duration_min, style)
    out_dir  = Path(out) if out else None
    out_path = export_notes(notes, topic, out_dir)

    console.print(f"\n[bold green]Notes saved to:[/] {out_path}")
    console.print("\n[dim]Preview (first 500 chars):[/]")
    console.print(notes[:500] + ("..." if len(notes) > 500 else ""))


# ── smoke-test ────────────────────────────────────────────────────────────────

@cli.command("smoke-test")
def smoke_test_cmd():
    """
    Run quick sanity checks on each pipeline stage.

    Does NOT require scraper data or a Claude API key.
    """
    from vedabase_notes_agent.eval.eval_smoke import run_smoke_test
    passed = run_smoke_test()
    raise SystemExit(0 if passed else 1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
