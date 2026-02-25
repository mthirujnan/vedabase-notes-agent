"""
eval_smoke.py
-------------
Smoke test — a quick sanity check that each pipeline stage works.

Beginner tip — what is a smoke test?
  A smoke test is the simplest possible test: just make sure nothing
  "catches fire" (crashes) when you run the code. It's not testing
  correctness deeply — just that the plumbing connects properly.

  Like turning on a new appliance for the first time: if smoke comes
  out, something is wrong!

Run with:
  python -m vedabase_notes_agent.cli smoke-test
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# A minimal fake verse for testing without running the full scraper
SAMPLE_VERSE = {
    "id":             "NOI-TEST",
    "book":           "NOI",
    "verse_number":   "1",
    "verse_sanskrit": "vāco vegaṁ manasaḥ krodha-vegaṁ",
    "translation":    (
        "A sober person who can tolerate the urge to speak, the mind's demands, "
        "the actions of anger and the urges of the tongue, belly and genitals is "
        "qualified to make disciples all over the world."
    ),
    "purport": (
        "Gosvāmī means one who can control the senses and mind. "
        "The six Gosvāmīs of Vṛndāvana were great sages who controlled all urges. "
        "A person who has learned to control the tongue, belly and genitals is "
        "qualified to be called gosvāmī and can accept disciples anywhere."
    ),
    "section_title":  "Text 1 (TEST)",
    "source_uri":     "https://vedabase.io/en/library/noi/1/",
}


def run_smoke_test() -> bool:
    """
    Run all smoke tests. Returns True if all pass, False otherwise.
    """
    console.print("\n[bold cyan]Running smoke tests...[/]\n")

    results = []
    results.append(_test_chunker())
    results.append(_test_embedder())
    results.append(_test_retriever())
    results.append(_test_verifier())

    # Print summary table
    table = Table(title="Smoke Test Results")
    table.add_column("Test",   style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Detail")

    all_passed = True
    for name, passed, detail in results:
        status = "[green]PASS[/]" if passed else "[red]FAIL[/]"
        table.add_row(name, status, detail)
        if not passed:
            all_passed = False

    console.print(table)

    if all_passed:
        console.print("\n[bold green]All smoke tests passed![/]")
    else:
        console.print("\n[bold red]Some tests failed. See details above.[/]")

    return all_passed


def _test_chunker() -> tuple[str, bool, str]:
    """Test that the chunker produces valid chunks from a sample verse."""
    try:
        from vedabase_notes_agent.chunk.chunk_text import _chunk_record
        chunks = _chunk_record(SAMPLE_VERSE)
        assert len(chunks) >= 1, "No chunks produced"
        assert all("chunk_id" in c and "text" in c for c in chunks), \
            "Chunks missing required fields"
        assert all(len(c["text"]) > 10 for c in chunks), \
            "Chunks are too short"
        return ("Chunker", True, f"{len(chunks)} chunks produced OK")
    except Exception as e:
        return ("Chunker", False, str(e))


def _test_embedder() -> tuple[str, bool, str]:
    """Test that the embedding model loads and produces vectors."""
    try:
        from vedabase_notes_agent.index.embed import embed_texts
        vecs = embed_texts(["A sober person who can tolerate the urge to speak."])
        assert len(vecs) == 1, "Expected 1 vector"
        assert len(vecs[0]) > 0, "Vector is empty"
        assert isinstance(vecs[0][0], float), "Vector values should be floats"
        return ("Embedder", True, f"Vector dim={len(vecs[0])}")
    except Exception as e:
        return ("Embedder", False, str(e))


def _test_retriever() -> tuple[str, bool, str]:
    """Test that ChromaDB is accessible (even if empty)."""
    try:
        from vedabase_notes_agent.index.vector_store import collection_size
        size = collection_size()
        return ("Vector DB", True, f"{size} chunks indexed")
    except Exception as e:
        return ("Vector DB", False, str(e))


def _test_verifier() -> tuple[str, bool, str]:
    """Test that the rule-based verifier catches missing citations."""
    try:
        from vedabase_notes_agent.agent.verifier import rule_check

        # Notes without citations should fail
        bad_notes = "## Outline\n## Detailed Notes\nSome point without citation.\n"
        result = rule_check(bad_notes)
        assert not result["pass"], "Should fail — no citations"

        # Notes with citations should pass citation check
        good_notes = (
            "## Outline\n## Detailed Notes\n"
            "Key point. [NOI 1 Translation]\n"
            "Another point. [NOI 3 Purport]\n"
            "Third point. [NOI 2 Purport]\n"
            "## Practical Applications\n## Discussion Prompts\n## Appendix\n"
        )
        result2 = rule_check(good_notes)
        assert result2["citations_ok"], "Should pass citation check"
        return ("Verifier", True, "Citation check logic works")
    except Exception as e:
        return ("Verifier", False, str(e))
