"""
prompts.py
----------
All prompt templates used by the agent.

Keeping prompts in one file makes them easy to tune without
touching the agent logic. Think of this as the "script" for
the AI — what instructions we give Claude at each step.
"""


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a faithful teaching assistant specialising in the Nectar of Instruction
(Śrī Upadeśāmṛta) by Śrīla Rūpa Gosvāmī with commentary by Śrīla Prabhupāda.

Your role:
- Help prepare study notes and class outlines
- Ground every statement in the provided source passages
- Cite every key point with the format [NOI <verse> <section>]
  e.g. [NOI 1 Translation], [NOI 3 Purport], [NOI Preface]
- Never add information not found in the provided context
- If the context is insufficient for a point, say so explicitly

Citation format rules:
  [NOI 1 Translation]   — for a verse's translation
  [NOI 3 Purport]       — for the commentary
  [NOI Preface]         — for the preface
"""


# ── Step (a): Plan an outline ─────────────────────────────────────────────────

PLAN_PROMPT = """\
Based on the following retrieved passages from the Nectar of Instruction,
create a structured outline for a {style} on the topic: "{topic}"

Audience: {audience}
Duration: {duration} minutes

Retrieved passages:
{context}

Produce a numbered outline with 3-6 main sections and estimated time per section.
Each section must be supported by at least one citation from the passages above.
Format: plain text outline only — no notes yet.
"""


# ── Step (b): Draft the full notes ───────────────────────────────────────────

DRAFT_PROMPT = """\
Using the outline below and the retrieved passages, write complete study notes
for a {style} on: "{topic}"

Audience: {audience}
Duration: {duration} minutes

Outline:
{outline}

Retrieved passages (use these as your only source — cite everything):
{context}

Follow this exact template:

---
# {topic}

**Audience:** {audience}
**Duration:** {duration} minutes
**Style:** {style}

## Outline
{outline}

## Detailed Notes

[For each section in the outline, write 3-5 key points.
 Each key point MUST end with a citation like [NOI 3 Purport].]

## Practical Applications
1. [First application with citation]
2. [Second application with citation]
3. [Third application with citation]

## Discussion Prompts
1. [Question that draws out the verse's meaning]
2. [Question connecting the teaching to daily life]
3. [Question on how to practically apply this]
4. [Deeper philosophical question]
5. [Question for self-reflection]

## Appendix: Key Passages
[Include 3-5 short direct quotes from the retrieved passages.
 Each quote must be ≤ {excerpt_max} characters and end with its citation.
 Format: > "quote text" — [NOI X Section]]
---

Important: every key point and application MUST contain a citation.
Do not invent information. If the passages don't support a point, omit it.
"""


# ── Step (c): Verification prompt ────────────────────────────────────────────

VERIFY_PROMPT = """\
Review the following study notes for the Nectar of Instruction.
Check each requirement and respond with a JSON object only (no other text):

Requirements to check:
1. Every key point has a citation in format [NOI X Section]
2. The notes contain all required sections:
   - Outline, Detailed Notes, Practical Applications,
     Discussion Prompts, Appendix: Key Passages
3. No excerpt in the Appendix exceeds {excerpt_max} characters
4. No claims are made without citation support

Respond with this exact JSON:
{{
  "all_points_cited": true/false,
  "required_sections_present": true/false,
  "excerpts_within_limit": true/false,
  "issues": ["list any problems found, or empty list if none"],
  "pass": true/false
}}

Notes to verify:
{notes}
"""
