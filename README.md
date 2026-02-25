# Vedabase Notes Agent

A local AI agent that reads the **Nectar of Instruction** (Śrī Upadeśāmṛta)
and helps you prepare study notes and class outlines — with every point
backed by a cited verse or purport.

**Example output:**
> "One who can control the tongue, belly, and genitals is a gosvāmī,
>  qualified to accept disciples anywhere in the world. [NOI 1 Translation]"

---

## What this system does (plain English)

1. **Reads the book** — fetches all 12 sections from vedabase.io
2. **Understands the text** — converts each passage into numbers (embeddings)
   that capture the *meaning* of the text
3. **Stores it locally** — saves everything to your laptop in a local database
4. **Answers your requests** — when you ask for notes on "controlling the senses",
   it finds the most relevant passages and asks Claude to write structured notes
5. **Verifies the output** — checks that every point has a citation before saving

---

## What is RAG? (Beginner explanation)

**RAG = Retrieval Augmented Generation**

The problem: Claude (the AI) hasn't memorised the Nectar of Instruction perfectly.
The solution: Before asking Claude to write anything, we *retrieve* the most
relevant passages from our local database and paste them into Claude's context.
Claude then writes notes grounded in the actual text.

```
Your query: "notes on six urges"
      ↓
Retriever: searches local DB → finds 8 most relevant passages
      ↓
Agent: pastes passages into Claude's prompt
      ↓
Claude: writes notes citing [NOI 1 Translation], [NOI 2 Purport], etc.
      ↓
Verifier: checks every point has a citation
      ↓
Your notes are saved to data/outputs/
```

---

## System map

```
vedabase-notes-agent/
  src/vedabase_notes_agent/
    ingest/       ← Step 1: fetch raw book content (wraps existing scraper)
    parse/        ← Step 2: extract verse number, Sanskrit, translation, purport
    chunk/        ← Step 3: split into small pieces for the database
    index/        ← Step 4: embed chunks + store in ChromaDB
    retrieve/     ← finds relevant chunks at query time
    agent/        ← the AI loop: plan → draft → verify
    export/       ← saves notes as Markdown files
    eval/         ← smoke tests
    cli.py        ← all commands live here
  data/           ← all generated data (gitignored — stays on your laptop)
  tests/          ← automated tests
```

---

## How the scraper is reused

This project does **not** contain a scraper. Instead, it wraps the one
you already built in the `noi-search` project.

**How it works:**

```
noi-search/scraper.py          ← your existing scraper (not modified)
         ↓
src/ingest/ingest_noi.py       ← thin wrapper that calls scraper.scrape()
         ↓
data/raw/noi/noi_raw.json      ← raw data saved here
```

The wrapper tries three strategies:
1. If `NOI_SCRAPER_PATH` is set → imports and runs the scraper
2. If `data.json` exists next to the scraper → copies it
3. Otherwise → clear instructions on what to do

---

## Setup (step by step)

### 1. Install Python dependencies

```bash
# Create a clean conda environment (run once)
conda create -n vedabase-agent python=3.11 -y
conda run -n vedabase-agent pip install -r requirements.txt
```

### 2. Configure your environment

```bash
cp .env.example .env
```

Open `.env` and fill in:
- `CLAUDE_API_KEY` — from https://console.anthropic.com
- `NOI_SCRAPER_PATH` — path to your noi-search scraper:
  `/Users/muthukumar/Desktop/Claude Projects/noi-search/scraper.py`

### 3. Run the pipeline (one command at a time)

```bash
# Step 1 — Fetch the book (calls your existing scraper)
python -m vedabase_notes_agent.cli ingest-noi

# Step 2 — Parse into structured records
python -m vedabase_notes_agent.cli parse --book NOI

# Step 3 — Split into chunks
python -m vedabase_notes_agent.cli chunk --book NOI

# Step 4 — Embed and store in local vector DB
#           (downloads ~90 MB embedding model on first run)
python -m vedabase_notes_agent.cli index --book NOI

# Step 5 — Generate notes! (requires CLAUDE_API_KEY)
python -m vedabase_notes_agent.cli generate-notes \
  --topic "controlling the six urges" \
  --audience "new students" \
  --duration-min 60 \
  --style class
```

Your notes appear in `data/outputs/notes_<topic>_<date>.md`

### 4. Run smoke tests (no API key needed)

```bash
python -m vedabase_notes_agent.cli smoke-test
```

### 5. Run unit tests

```bash
python -m pytest tests/ -v
```

---

## CLI Reference

| Command | What it does |
|---------|-------------|
| `ingest-noi` | Fetch raw content using existing scraper |
| `parse --book NOI` | Extract structured fields from raw text |
| `chunk --book NOI` | Split into DB-sized pieces |
| `index --book NOI` | Embed + store in ChromaDB |
| `generate-notes --topic "..."` | Full agent: retrieve → plan → draft → verify → save |
| `smoke-test` | Quick sanity check on all stages |

---

## Adding other Vedabase books

To add, say, *Bhagavad-gītā As It Is*:

1. **Extend the scraper** in `noi-search/scraper.py` to include BG pages,
   or create a new scraper for BG

2. **Create a parser** at `src/parse/parse_bg.py` following the same pattern
   as `parse_noi.py`

3. **Register the book** in `cli.py` — add `"BG"` to the `--book` options

4. **Ingest and index** the new book:
   ```bash
   python -m vedabase_notes_agent.cli ingest-bg
   python -m vedabase_notes_agent.cli parse --book BG
   python -m vedabase_notes_agent.cli chunk --book BG
   python -m vedabase_notes_agent.cli index --book BG
   ```

5. **Generate notes** using `--book BG --topic "..."`

The architecture is designed so each book is a separate "lane" through
the same pipeline stages.

---

## Data stored on your laptop

All data is local — nothing is sent to any cloud storage:

```
data/
  raw/noi/noi_raw.json     ← raw pages from scraper
  clean/noi_clean.jsonl    ← structured verse records
  chunks/noi_chunks.jsonl  ← text chunks ready for embedding
  index/                   ← ChromaDB vector database files
  outputs/                 ← generated notes (Markdown)
```

The `data/` folder is gitignored so your notes stay private.

---

## Respecting Vedabase Terms

- The scraper adds a 1-second delay between requests (polite crawling)
- Content is fetched once and cached locally — not re-fetched repeatedly
- This app is for personal study only — not for redistribution
- Always check https://vedabase.io/robots.txt before running the scraper

---

## Troubleshooting

**"Cannot find scraped data"**
→ Set `NOI_SCRAPER_PATH` in `.env` or copy `data.json` manually

**"CLAUDE_API_KEY is not set"**
→ Add your key to `.env` — get one at https://console.anthropic.com

**"No chunks found in the vector database"**
→ Run the pipeline in order: ingest → parse → chunk → index

**Embedding model download is slow**
→ First run only. The model (~90 MB) is cached in `~/.cache/huggingface/`

**Tests fail with import errors**
→ Make sure your virtualenv is active: `source .venv/bin/activate`
