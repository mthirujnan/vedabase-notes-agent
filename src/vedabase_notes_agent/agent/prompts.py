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
You are a faithful teaching assistant specialising in Śrīla Prabhupāda's books,
especially the Nectar of Instruction (Śrī Upadeśāmṛta) by Śrīla Rūpa Gosvāmī.

Your role:
- Help prepare study notes, class outlines, and discourse guides
- Primary citations come from the retrieved NOI passages provided to you
- You may ALSO draw on your knowledge of other Śrīla Prabhupāda books to
  supplement — Bhagavad-gītā As It Is (BG), Śrīmad-Bhāgavatam (SB),
  Caitanya-caritāmṛta (CC), Nectar of Devotion (NOD), etc.
- Include 2-3 illustrative stories or Vedic pastimes that strengthen the teaching
- Cite every statement clearly

Citation format rules:
  Primary (from retrieved text):
    [NOI 1 Translation], [NOI 3 Purport], [NOI Preface]

  Supplemental (from your knowledge of other books):
    [BG 6.5 Purport], [SB 11.2.45 Purport], [CC Madhya 22.54],
    [NOD Ch.8], [BG 3.42 Translation] — use chapter/verse where known

  Stories:
    Attribute clearly: "In the pastime of..." or "Śrīla Prabhupāda tells..."
    End with source if known: [SB 9.4.18–20], [CC Antya 6], etc.
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
Include one section for stories/pastimes and one for practical application.
Each section should note which source (NOI verse or other book) will support it.
Format: plain text outline only — no notes yet.
"""


# ── Step (b): Draft the full notes ───────────────────────────────────────────

DRAFT_PROMPT = """\
Using the outline and retrieved passages, write complete study notes
for a {style} on: "{topic}"

Audience: {audience}
Duration: {duration} minutes

Outline:
{outline}

Retrieved NOI passages (these are your PRIMARY source — cite everything from here):
{context}

You may ALSO use your knowledge of other Śrīla Prabhupāda books
(BG, SB, CC, NOD, etc.) to add SUPPLEMENTAL supporting references.

CRITICAL: You MUST complete EVERY section below. Keep each section concise so you
do not run out of space. Do NOT write lengthy paragraphs — use tight, punchy points.
Complete all sections even if brief. An incomplete document is useless.

Output the following template exactly, filling in every section:

---
# {topic}

**Audience:** {audience}
**Duration:** {duration} minutes
**Style:** {style}

## Outline
{outline}

## Detailed Notes

[For EACH section in the outline write 2-3 key points (not more).
 Each point is 1-2 sentences MAX, ending with its citation.
 Primary: [NOI 3 Purport]  Supplemental: [BG 6.5 Purport] or [SB 11.2.45 Purport]]

## Stories & Pastimes

### Story 1: [Title]
[80-120 words. Vivid, connected to topic. End: *Lesson: ...* [Source citation]]

### Story 2: [Title]
[80-120 words. Devotee example or Prabhupāda anecdote. End: *Lesson: ...* [Source]]

### Story 3: [Title]
[80-120 words. Only if genuinely relevant — otherwise write "N/A — two stories sufficient."]

## Supplemental References from Śrīla Prabhupāda's Other Books

**[Citation 1]** "One-sentence quote or teaching."
**[Citation 2]** "One-sentence quote or teaching."
**[Citation 3]** "One-sentence quote or teaching."
**[Citation 4]** "One-sentence quote or teaching." *(optional)*
**[Citation 5]** "One-sentence quote or teaching." *(optional)*

## Practical Applications
1. [One sentence + citation]
2. [One sentence + citation]
3. [One sentence + citation]

## Discussion Prompts
1. [Question drawing out the verse's meaning]
2. [Question connecting teaching to daily life]
3. [Question on practical application]
4. [Deeper philosophical question]
5. [Self-reflection question]

## Appendix: Key NOI Passages
> "[Quote ≤ {excerpt_max} chars]" — [NOI X Section]
> "[Quote ≤ {excerpt_max} chars]" — [NOI X Section]
> "[Quote ≤ {excerpt_max} chars]" — [NOI X Section]
---

Rules:
- Every key point MUST have a citation
- Stories end with *Lesson: ...* and a source
- Do not invent exact quotes — paraphrase and note it
- FINISH every section — an unfinished document fails verification
"""


# ── Step (c): Verification prompt ────────────────────────────────────────────

VERIFY_PROMPT = """\
Review the following study notes. Check each requirement and respond
with a JSON object only (no other text):

Requirements to check:
1. Every key point has a citation [NOI X Section] or [Book X.X]
2. All required sections are present:
   Outline, Detailed Notes, Stories & Pastimes,
   Supplemental References, Practical Applications,
   Discussion Prompts, Appendix
3. At least 2 stories are included
4. At least 3 supplemental references from other books
5. No excerpt in the Appendix exceeds {excerpt_max} characters

Respond with this exact JSON:
{{
  "all_points_cited": true/false,
  "required_sections_present": true/false,
  "stories_included": true/false,
  "supplemental_refs_included": true/false,
  "excerpts_within_limit": true/false,
  "issues": ["list any problems found, or empty list if none"],
  "pass": true/false
}}

Notes to verify:
{notes}
"""
