"""
Browse Book page — search the Nectar of Instruction directly.

Uses semantic search (same as the agent uses internally) so plain English
queries match Sanskrit terms with diacritics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from vedabase_notes_agent.config import CLEAN_DIR

st.set_page_config(page_title="Browse Book — Vedabase", page_icon="🔍", layout="wide")
st.title("🔍 Browse the Book")
st.markdown(
    "Search the Nectar of Instruction by meaning — not just exact words. "
    "Plain English finds Sanskrit terms automatically."
)
st.divider()

# ── Check if vector DB is ready ───────────────────────────────────────────────

try:
    from vedabase_notes_agent.index.vector_store import collection_size
    db_ready = collection_size() > 0
except Exception:
    db_ready = False

# ── Search bar ────────────────────────────────────────────────────────────────

col_search, col_k = st.columns([5, 1])

with col_search:
    query = st.text_input(
        "Search",
        placeholder="e.g. controlling the tongue, qualities of a teacher, Vrindavana...",
        label_visibility="collapsed",
    )

with col_k:
    top_k = st.selectbox("Results", [4, 8, 12, 16], index=1, label_visibility="visible")

# ── Filter by verse ───────────────────────────────────────────────────────────

verse_options = ["All"] + ["Preface"] + [f"Text {i}" for i in range(1, 12)]
filter_verse  = st.pills("Filter by text", verse_options, default="All")

st.divider()

# ── Search execution ──────────────────────────────────────────────────────────

def normalize(s: str) -> str:
    """Strip diacritics so plain English matches Sanskrit."""
    import unicodedata
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


if query.strip():
    if not db_ready:
        st.warning("Vector DB not indexed yet. Run the **⚙️ Pipeline** steps first.", icon="⚠️")
        st.stop()

    try:
        from vedabase_notes_agent.retrieve.retriever import retrieve

        hits = retrieve(query.strip(), top_k=top_k)

        # Apply verse filter
        if filter_verse != "All":
            filter_id = "preface" if filter_verse == "Preface" else filter_verse.split()[-1]
            hits = [h for h in hits if h["verse_number"] == filter_id]

        if not hits:
            st.info("No results found. Try different words or remove the filter.")
        else:
            st.caption(f"{len(hits)} result(s) for **\"{query}\"**")

            for hit in hits:
                verse   = hit["verse_number"]
                section = hit["section"].capitalize()
                uri     = hit["source_uri"]
                text    = hit["text"]

                # Build citation label
                if verse == "preface":
                    label = "NOI Preface"
                else:
                    label = f"NOI Text {verse}"

                with st.container(border=True):
                    hcol1, hcol2 = st.columns([4, 1])
                    with hcol1:
                        st.markdown(f"**{label}** — *{section}*")
                    with hcol2:
                        st.link_button("Read on vedabase.io ↗", uri, use_container_width=True)

                    # Highlight query words in the snippet
                    query_words = normalize(query.lower()).split()
                    highlighted = text
                    for word in query_words:
                        if len(word) > 2:
                            # Find and wrap matching words (diacritic-insensitive)
                            import re
                            def highlight_match(m):
                                return f"**{m.group(0)}**"
                            pattern = re.compile(
                                r'\b\w*' + re.escape(word) + r'\w*\b', re.IGNORECASE
                            )
                            # Apply on normalized version to find positions, show original
                            words_list = highlighted.split()
                            result_words = []
                            for w in words_list:
                                if word in normalize(w.lower()):
                                    result_words.append(f"**{w}**")
                                else:
                                    result_words.append(w)
                            highlighted = " ".join(result_words)

                    st.markdown(highlighted[:800] + ("..." if len(text) > 800 else ""))

                    # Relevance score
                    score = 1 - hit.get("distance", 0.5)
                    st.caption(f"Relevance: {score:.0%}")

    except Exception as e:
        st.error(f"Search error: {e}")

else:
    # No query yet — show a browse-by-verse table of contents
    st.markdown("#### Or browse by verse")

    clean_path = CLEAN_DIR / "noi_clean.jsonl"
    if clean_path.exists():
        import json
        records = []
        with open(clean_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        for rec in records:
            with st.expander(
                f"**{rec['section_title']}**"
                + (f" — {rec['translation'][:80]}..." if rec.get('translation') else ""),
                expanded=False,
            ):
                if rec.get("verse_sanskrit"):
                    st.markdown(f"*{rec['verse_sanskrit']}*")
                    st.divider()

                if rec.get("translation"):
                    st.markdown(f"**Translation:** {rec['translation']}")

                if rec.get("purport"):
                    purport_preview = rec["purport"][:500]
                    if len(rec["purport"]) > 500:
                        purport_preview += "..."
                    st.markdown(f"**Purport:** {purport_preview}")

                st.link_button(
                    f"Read full text on vedabase.io ↗",
                    rec["source_uri"],
                )
    else:
        st.info(
            "Run the **⚙️ Pipeline** → Parse step to browse verses.",
            icon="💡",
        )

# ── Sidebar tips ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 💡 Search Tips")
    st.markdown("""
- Plain English finds Sanskrit:
  `gosvami` → finds *Gosvāmī*
  `Krishna` → finds *Kṛṣṇa*

- Search by concept:
  `sense control`
  `qualities of a disciple`
  `holy name`

- Search by place:
  `Vrindavana`
  `Mathura`
""")
    st.divider()
    st.markdown("### Quick Searches")
    quick = [
        "controlling the senses",
        "qualities of a spiritual master",
        "chanting the holy name",
        "Vrindavana dhama",
        "offenses to be avoided",
    ]
    for q in quick:
        if st.button(q, key=f"quick_{q}", use_container_width=True):
            st.query_params["q"] = q
            st.rerun()

# ── Background jobs sidebar ─────────────────────────────────────────────────
from vedabase_notes_agent.ui_jobs import show_jobs_sidebar
show_jobs_sidebar()
