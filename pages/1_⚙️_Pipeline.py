"""
Pipeline page — run the ingestion and indexing steps.

Each step must be completed in order before generating notes.
Steps only need to be run once (data persists in data/ folder).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from vedabase_notes_agent.config import RAW_DIR, CLEAN_DIR, CHUNKS_DIR

st.set_page_config(page_title="Pipeline — Vedabase Notes", page_icon="⚙️", layout="wide")
st.title("⚙️ Pipeline Setup")
st.markdown(
    "Run each step once to prepare the book. "
    "Steps are saved to your `data/` folder and don't need to be repeated."
)
st.divider()

# ── Helper: status badge ──────────────────────────────────────────────────────

def status_badge(ok: bool, ok_label: str, fail_label: str) -> str:
    return f"✅ {ok_label}" if ok else f"⬜ {fail_label}"


# ── Check current state ───────────────────────────────────────────────────────

raw_path    = RAW_DIR    / "noi" / "noi_raw.json"
clean_path  = CLEAN_DIR  / "noi_clean.jsonl"
chunks_path = CHUNKS_DIR / "noi_chunks.jsonl"

raw_ok    = raw_path.exists()
clean_ok  = clean_path.exists()
chunks_ok = chunks_path.exists()

try:
    from vedabase_notes_agent.index.vector_store import collection_size
    db_size = collection_size()
    db_ok   = db_size > 0
except Exception:
    db_ok   = False
    db_size = 0


# ── Step cards ────────────────────────────────────────────────────────────────

def step_card(num, title, description, status_ok, ok_detail, fail_detail):
    """Render a pipeline step card with status and a run button."""
    with st.container(border=True):
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            icon = "✅" if status_ok else "⬜"
            st.markdown(f"#### {icon} Step {num}: {title}")
            st.caption(description)
            if status_ok:
                st.success(ok_detail, icon="✓")
            else:
                st.info(fail_detail, icon="ℹ️")
        with col_btn:
            st.write("")  # vertical spacing
            return st.button(
                "Run" if not status_ok else "Re-run",
                key=f"step_{num}",
                type="primary" if not status_ok else "secondary",
                use_container_width=True,
            )


# ── Step 1: Ingest ────────────────────────────────────────────────────────────

run1 = step_card(
    1, "Ingest",
    "Fetches all 12 pages from vedabase.io using the existing noi-search scraper.",
    raw_ok,
    f"Data saved at `{raw_path.relative_to(Path.cwd()) if raw_path.exists() else raw_path}`",
    "Raw data not found. Click **Run** to fetch from vedabase.io.",
)

if run1:
    with st.status("Fetching book content from vedabase.io...", expanded=True) as status:
        try:
            from vedabase_notes_agent.ingest.ingest_noi import ingest_noi
            st.write("Calling existing scraper from noi-search project...")
            result = ingest_noi()
            st.write(f"Saved to: `{result}`")
            status.update(label="Ingest complete!", state="complete")
            st.rerun()
        except Exception as e:
            status.update(label="Ingest failed", state="error")
            st.error(str(e))


# ── Step 2: Parse ─────────────────────────────────────────────────────────────

run2 = step_card(
    2, "Parse",
    "Extracts verse number, Sanskrit, translation, and purport from each page.",
    clean_ok,
    f"`{clean_path.name}` ready — structured verse records",
    "Needs Step 1 to complete first.",
)

if run2:
    if not raw_ok:
        st.error("Complete Step 1 (Ingest) first.")
    else:
        with st.status("Parsing verse structure...", expanded=True) as status:
            try:
                from vedabase_notes_agent.parse.parse_noi import parse_noi
                result = parse_noi()

                # Show a preview of parsed records
                import json
                records = []
                with open(result) as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))

                st.write(f"Parsed **{len(records)} records**")
                if records:
                    st.dataframe(
                        [{"id": r["id"], "verse": r["verse_number"],
                          "translation_preview": r["translation"][:80] + "..."
                          if len(r.get("translation","")) > 80 else r.get("translation","")}
                         for r in records],
                        use_container_width=True,
                    )
                status.update(label="Parse complete!", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label="Parse failed", state="error")
                st.error(str(e))


# ── Step 3: Chunk ─────────────────────────────────────────────────────────────

run3 = step_card(
    3, "Chunk",
    "Splits each verse into smaller pieces (translation chunk + purport chunks) for the vector DB.",
    chunks_ok,
    f"`{chunks_path.name}` ready",
    "Needs Step 2 to complete first.",
)

if run3:
    if not clean_ok:
        st.error("Complete Step 2 (Parse) first.")
    else:
        with st.status("Splitting text into chunks...", expanded=True) as status:
            try:
                from vedabase_notes_agent.chunk.chunk_text import chunk_noi
                result = chunk_noi()
                status.update(label="Chunk complete!", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label="Chunk failed", state="error")
                st.error(str(e))


# ── Step 4: Index ─────────────────────────────────────────────────────────────

run4 = step_card(
    4, "Index (Embed + Store)",
    "Converts each chunk into a vector embedding and stores it in the local ChromaDB database. "
    "Downloads the embedding model (~90 MB) on first run.",
    db_ok,
    f"**{db_size} chunks** indexed in ChromaDB",
    "Needs Step 3 to complete first. First run downloads ~90 MB model.",
)

if run4:
    if not chunks_ok:
        st.error("Complete Step 3 (Chunk) first.")
    else:
        with st.status("Embedding chunks and building vector index...", expanded=True) as status:
            try:
                from vedabase_notes_agent.chunk.chunk_text import load_chunks
                from vedabase_notes_agent.index.vector_store import index_chunks, collection_size

                st.write("Loading chunks...")
                all_chunks = load_chunks()
                st.write(f"Loaded **{len(all_chunks)} chunks**. Embedding now (this may take a minute)...")

                index_chunks(all_chunks)
                final_size = collection_size()

                st.write(f"✅ {final_size} chunks now in vector DB")
                status.update(label=f"Index complete! ({final_size} chunks)", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label="Index failed", state="error")
                st.error(str(e))


# ── Run all button ────────────────────────────────────────────────────────────

st.divider()

all_done = raw_ok and clean_ok and chunks_ok and db_ok

if all_done:
    st.success(
        "🎉 All pipeline steps complete! Head to **📝 Generate Notes** to create your first notes.",
        icon="✅",
    )
else:
    if st.button("▶ Run All Incomplete Steps", type="primary", use_container_width=True):
        with st.status("Running full pipeline...", expanded=True) as status:
            try:
                if not raw_ok:
                    st.write("Step 1: Ingesting...")
                    from vedabase_notes_agent.ingest.ingest_noi import ingest_noi
                    ingest_noi()

                if not clean_ok:
                    st.write("Step 2: Parsing...")
                    from vedabase_notes_agent.parse.parse_noi import parse_noi
                    parse_noi()

                if not chunks_ok:
                    st.write("Step 3: Chunking...")
                    from vedabase_notes_agent.chunk.chunk_text import chunk_noi
                    chunk_noi()

                st.write("Step 4: Indexing (this takes a moment)...")
                from vedabase_notes_agent.chunk.chunk_text import load_chunks
                from vedabase_notes_agent.index.vector_store import index_chunks, collection_size
                index_chunks(load_chunks())
                n = collection_size()

                status.update(label=f"Pipeline complete! {n} chunks indexed.", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label="Pipeline failed", state="error")
                st.error(str(e))
