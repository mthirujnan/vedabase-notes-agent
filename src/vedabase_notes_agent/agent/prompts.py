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
 Each key point MUST end with a citation.
 Primary: [NOI 3 Purport] — Supplemental: [BG 6.5 Purport] or [SB 11.2.45]]

## Stories & Pastimes

### Story 1: [Title]
[Tell the story in 100-150 words. Make it vivid and connected to the topic.
 End with: *Lesson: ...* and cite the source e.g. [SB 9.4.18–20] or [CC Antya 6]]

### Story 2: [Title]
[Second story — can be a direct pastime of Kṛṣṇa, a devotee's example,
 or an anecdote Śrīla Prabhupāda used in his lectures.
 End with: *Lesson: ...* and source citation]

### Story 3: [Title — only if strongly relevant to topic]
[Optional third story. Omit this section if a third story would feel forced.]

## Supplemental References from Śrīla Prabhupāda's Other Books
[List 3-5 relevant quotes or teachings from BG, SB, CC, NOD, etc.
 that deepen the topic. Format each as:
 **[Book Citation]** "Quote or teaching in one sentence." ]

## Practical Applications
1. [Application with citation — how to apply this teaching today]
2. [Application with citation]
3. [Application with citation]

## Discussion Prompts
1. [Question that draws out the verse's meaning]
2. [Question connecting the teaching to daily life]
3. [Question on how to practically apply this]
4. [Deeper philosophical question]
5. [Question for self-reflection]

## Appendix: Key NOI Passages
[Include 3-5 short direct quotes from the retrieved NOI passages.
 Each quote must be ≤ {excerpt_max} characters and end with its citation.
 Format: > "quote text" — [NOI X Section]]
---

Important:
- Every key point MUST contain a citation (NOI or other book)
- Stories must feel natural and directly connected to the topic
- Do not invent quotes — if unsure of exact wording, paraphrase and note it
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
