"""
app.py — Vedabase Notes Agent UI
---------------------------------
Entry point for the Streamlit web interface.

Run with:
    streamlit run app.py

Or use the CLI shortcut:
    python -m vedabase_notes_agent.cli ui
"""

import sys
from pathlib import Path

# Add src/ to Python path so all our modules are importable
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st

st.set_page_config(
    page_title="Vedabase Notes Agent",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Home page ─────────────────────────────────────────────────────────────────

st.title("📖 Vedabase Notes Agent")
st.markdown("### *Nectar of Instruction — Study Notes with Citations*")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### What this tool does
    This agent reads the **Nectar of Instruction** by Śrīla Prabhupāda
    and helps you prepare study notes, class outlines, and discourse guides —
    with every point backed by a cited verse or purport.

    Every key point looks like this:
    > *"One who can control the tongue, belly, and genitals is a gosvāmī,
    qualified to accept disciples everywhere."*
    > **[NOI 1 Translation]**
    """)

with col2:
    st.markdown("""
    #### How to get started

    | Step | Page | What it does |
    |------|------|-------------|
    | 1 | ⚙️ **Pipeline** | Fetch, parse, and index the book |
    | 2 | 📝 **Generate** | Ask for notes on any topic |
    | 3 | 📚 **My Notes** | Browse saved notes |
    | 4 | 🔍 **Browse** | Search the book directly |

    *Run Pipeline first — it only needs to run once.*
    """)

st.divider()

# Quick status check on the sidebar
st.sidebar.markdown("### 📊 System Status")

from vedabase_notes_agent.config import RAW_DIR, CLEAN_DIR, CHUNKS_DIR

raw_ok    = (RAW_DIR    / "noi" / "noi_raw.json").exists()
clean_ok  = (CLEAN_DIR  / "noi_clean.jsonl").exists()
chunks_ok = (CHUNKS_DIR / "noi_chunks.jsonl").exists()

try:
    from vedabase_notes_agent.index.vector_store import collection_size
    db_size = collection_size()
    db_ok = db_size > 0
except Exception:
    db_ok   = False
    db_size = 0

st.sidebar.markdown(
    f"{'✅' if raw_ok    else '⬜'} Raw data\n\n"
    f"{'✅' if clean_ok  else '⬜'} Parsed records\n\n"
    f"{'✅' if chunks_ok else '⬜'} Chunks\n\n"
    f"{'✅' if db_ok     else '⬜'} Vector DB ({db_size} chunks)"
)

if not (raw_ok and clean_ok and chunks_ok and db_ok):
    st.sidebar.warning("⚙️ Pipeline not complete — go to **Pipeline** page first.")
else:
    st.sidebar.success("Ready to generate notes!")

from vedabase_notes_agent.config import CLAUDE_API_KEY
if not CLAUDE_API_KEY:
    st.sidebar.error("🔑 CLAUDE_API_KEY missing in .env")

# ── Background jobs sidebar ─────────────────────────────────────────────────
from vedabase_notes_agent.ui_jobs import show_jobs_sidebar
show_jobs_sidebar()
