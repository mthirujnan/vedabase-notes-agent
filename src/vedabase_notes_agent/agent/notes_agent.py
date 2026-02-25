"""
notes_agent.py
--------------
The main agent loop that orchestrates the full note-generation pipeline.

Beginner tip — what is an "agent loop"?
  An agent is a program that uses an LLM to make decisions and take actions.
  Our agent loop has 5 steps:

    (a) Plan    → ask Claude to outline the topic using retrieved passages
    (b) Retrieve → search the vector DB for relevant chunks
    (c) Draft   → ask Claude to write full notes using the outline + chunks
    (d) Verify  → check the notes meet quality rules (citations, sections)
    (e) Export  → save the notes as a markdown file

  Each step feeds into the next. The "loop" part means we can retry
  steps if something fails.
"""

import anthropic
from rich.console import Console
from rich.progress import track

from vedabase_notes_agent.config import (
    CLAUDE_API_KEY, CLAUDE_MODEL, EXCERPT_MAX_CHARS, MAX_TOKENS, TOP_K
)
from vedabase_notes_agent.retrieve.retriever import retrieve, format_context
from vedabase_notes_agent.agent.prompts import (
    SYSTEM_PROMPT, PLAN_PROMPT, DRAFT_PROMPT
)
from vedabase_notes_agent.agent.verifier import rule_check, llm_check

console = Console()


def generate_notes(
    topic:    str,
    audience: str = "general devotees",
    duration: int = 60,
    style:    str = "class",
) -> str:
    """
    Full agent pipeline. Returns the generated notes as a markdown string.

    Args:
        topic:    What the notes should cover (e.g. "controlling the senses")
        audience: Who the notes are for (e.g. "new students", "experienced devotees")
        duration: How long the class/discourse will be (minutes)
        style:    "class" (structured teaching) or "discourse" (flowing talk)
    """
    if not CLAUDE_API_KEY:
        raise ValueError(
            "CLAUDE_API_KEY is not set. Add it to your .env file.\n"
            "Get a key at: https://console.anthropic.com"
        )

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    # ── Step (a): Retrieve relevant chunks ───────────────────────────────────
    console.print(f"\n[cyan]Step 1/4:[/] Retrieving relevant passages for: [bold]{topic}[/]")
    hits = retrieve(topic, top_k=TOP_K)

    if not hits:
        raise RuntimeError(
            "No chunks found in the vector database. "
            "Have you run all pipeline steps? Try: chunk → index → generate-notes"
        )

    context = format_context(hits)
    console.print(f"  Found {len(hits)} relevant passages.")

    # ── Step (b): Plan an outline ─────────────────────────────────────────────
    console.print(f"\n[cyan]Step 2/4:[/] Planning outline...")
    outline = _call_claude(
        client,
        PLAN_PROMPT.format(
            topic=topic,
            audience=audience,
            duration=duration,
            style=style,
            context=context,
        ),
    )
    console.print("[dim]Outline complete.[/]")

    # ── Step (c): Draft the full notes ────────────────────────────────────────
    console.print(f"\n[cyan]Step 3/4:[/] Drafting notes...")
    notes = _call_claude(
        client,
        DRAFT_PROMPT.format(
            topic=topic,
            audience=audience,
            duration=duration,
            style=style,
            outline=outline,
            context=context,
            excerpt_max=EXCERPT_MAX_CHARS,
        ),
    )
    console.print("[dim]Draft complete.[/]")

    # ── Step (d): Verify ──────────────────────────────────────────────────────
    console.print(f"\n[cyan]Step 4/4:[/] Verifying notes quality...")

    # Rule-based check first (fast)
    rule_result = rule_check(notes)
    if rule_result["issues"]:
        console.print(f"[yellow]  Rule check issues:[/]")
        for issue in rule_result["issues"]:
            console.print(f"    • {issue}")
    else:
        console.print(
            f"  [green]Rule check passed.[/] "
            f"({rule_result['citation_count']} citations found)"
        )

    # LLM-based check (more thorough)
    llm_result = llm_check(notes)
    if not llm_result.get("pass", True):
        console.print("[yellow]  LLM check issues:[/]")
        for issue in llm_result.get("issues", []):
            console.print(f"    • {issue}")
    else:
        console.print("  [green]LLM check passed.[/]")

    # Attach a verification summary footer to the notes
    notes += _verification_footer(rule_result, llm_result)

    return notes


def _call_claude(client: anthropic.Anthropic, prompt: str) -> str:
    """
    Send a prompt to Claude and return the response text.

    This is a thin wrapper around the Anthropic API that handles
    the message format and extracts the text response.
    """
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _verification_footer(rule_result: dict, llm_result: dict) -> str:
    """
    Append a small summary section showing verification results.
    This helps the user know the notes were checked.
    """
    status = "PASSED" if (rule_result["pass"] and llm_result.get("pass", True)) else "WARNINGS"
    issues = rule_result["issues"] + llm_result.get("issues", [])

    footer = f"\n\n---\n\n## Verification ({status})\n"
    footer += f"- Citations found: {rule_result['citation_count']}\n"
    footer += f"- Sections check: {'✓' if rule_result['sections_ok'] else '✗'}\n"
    footer += f"- Excerpts check: {'✓' if rule_result['excerpts_ok'] else '✗'}\n"

    if issues:
        footer += "\n**Issues found:**\n"
        for issue in issues:
            footer += f"- {issue}\n"

    return footer
