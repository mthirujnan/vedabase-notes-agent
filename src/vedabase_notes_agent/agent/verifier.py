"""
verifier.py
-----------
Checks that generated notes meet quality requirements before saving.

Beginner tip — why verify?
  LLMs sometimes forget instructions (like "always add citations").
  A verifier is a second pass that catches problems before the notes
  reach the user. This is called "output validation" and is a key
  part of building reliable AI systems.

Two levels of verification:
  1. Rule-based (fast, no API call):
     - Count citations using regex
     - Check required section headings
     - Check excerpt lengths

  2. LLM-based (thorough, uses Claude):
     - Ask Claude to review its own output (self-critique)
     - Returns structured JSON with pass/fail + issues
"""

import json
import re

import anthropic

from vedabase_notes_agent.config import CLAUDE_API_KEY, CLAUDE_MODEL, EXCERPT_MAX_CHARS
from vedabase_notes_agent.agent.prompts import VERIFY_PROMPT, SYSTEM_PROMPT

# Sections that MUST appear in valid notes
REQUIRED_SECTIONS = [
    "## Outline",
    "## Detailed Notes",
    "## Practical Applications",
    "## Discussion Prompts",
    "## Appendix",
]

# Regex to find citations like [NOI 1 Translation] or [NOI Preface]
CITATION_RE = re.compile(r"\[NOI\s+\w+\s+\w+\]|\[NOI\s+Preface\]", re.IGNORECASE)


def rule_check(notes: str) -> dict:
    """
    Fast rule-based checks — no API call needed.

    Returns a dict with check results and a list of issues found.
    """
    issues = []

    # Check 1: All required sections present
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in notes]
    if missing_sections:
        issues.append(f"Missing sections: {missing_sections}")

    # Check 2: At least some citations exist
    citations = CITATION_RE.findall(notes)
    if len(citations) < 3:
        issues.append(
            f"Too few citations ({len(citations)} found — expected at least 3). "
            "Every key point should have a citation."
        )

    # Check 3: Appendix excerpts not too long
    # Find quoted passages between > " and " —
    excerpts = re.findall(r'>\s*"([^"]+)"', notes)
    long_excerpts = [e for e in excerpts if len(e) > EXCERPT_MAX_CHARS]
    if long_excerpts:
        issues.append(
            f"{len(long_excerpts)} excerpt(s) exceed {EXCERPT_MAX_CHARS} chars."
        )

    return {
        "sections_ok":    len(missing_sections) == 0,
        "citations_ok":   len(citations) >= 3,
        "excerpts_ok":    len(long_excerpts) == 0,
        "citation_count": len(citations),
        "issues":         issues,
        "pass":           len(issues) == 0,
    }


def llm_check(notes: str) -> dict:
    """
    Ask Claude to review the notes for quality.

    This is more thorough than rule-based but uses an API call.
    Returns a parsed JSON dict from Claude's response.
    """
    if not CLAUDE_API_KEY:
        return {"pass": True, "issues": ["LLM check skipped — no API key"]}

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    prompt = VERIFY_PROMPT.format(
        excerpt_max=EXCERPT_MAX_CHARS,
        notes=notes[:8000],  # truncate to avoid token limit
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Parse the JSON response from Claude
    try:
        # Sometimes Claude wraps JSON in ```json ... ``` — strip that
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "pass": False,
            "issues": [f"Could not parse verifier response: {raw[:200]}"],
        }
