"""
Generate Notes page — the main feature of the app.

Fill in a topic, audience, duration and style, hit Generate,
and the agent produces a full set of cited study notes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from vedabase_notes_agent.config import CLAUDE_API_KEY, CHUNKS_DIR

st.set_page_config(page_title="Generate Notes — Vedabase", page_icon="📝", layout="wide")
st.title("📝 Generate Notes")
st.markdown(
    "Describe your topic below. The agent will retrieve relevant passages "
    "from the Nectar of Instruction and write structured notes with citations."
)
st.divider()

# ── Guard: check pipeline is ready ───────────────────────────────────────────

try:
    from vedabase_notes_agent.index.vector_store import collection_size
    db_size = collection_size()
    pipeline_ready = db_size > 0
except Exception:
    pipeline_ready = False
    db_size = 0

if not pipeline_ready:
    st.warning(
        "The vector database is empty. "
        "Please complete the **⚙️ Pipeline** steps first.",
        icon="⚠️",
    )
    st.stop()

if not CLAUDE_API_KEY:
    st.error(
        "CLAUDE_API_KEY is not set. Add it to your `.env` file.\n\n"
        "Get a key at: https://console.anthropic.com",
        icon="🔑",
    )
    st.stop()

# ── Input form ────────────────────────────────────────────────────────────────

with st.form("notes_form"):
    st.subheader("What would you like notes on?")

    topic = st.text_input(
        "Topic *",
        placeholder="e.g. controlling the six urges, qualities of a Vaishnava, Vrindavana...",
        help="Be specific. The agent will search for the most relevant passages.",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        audience = st.text_input(
            "Audience",
            value="general devotees",
            help="Who is this for? e.g. new students, experienced practitioners",
        )

    with col2:
        duration = st.slider(
            "Duration (minutes)",
            min_value=15,
            max_value=120,
            value=60,
            step=15,
            help="How long is the class or discourse?",
        )

    with col3:
        style = st.radio(
            "Style",
            options=["class", "discourse"],
            help="Class = structured lecture with clear sections. Discourse = flowing presentation.",
        )

    submitted = st.form_submit_button(
        "✨ Generate Notes",
        type="primary",
        use_container_width=True,
    )

# ── Generation ────────────────────────────────────────────────────────────────

if submitted:
    if not topic.strip():
        st.error("Please enter a topic.")
        st.stop()

    # Store inputs in session so the result page can show them
    st.session_state["last_topic"]    = topic
    st.session_state["last_audience"] = audience
    st.session_state["last_duration"] = duration
    st.session_state["last_style"]    = style

    with st.status("🤖 Agent is working...", expanded=True) as status:
        try:
            st.write(f"**Topic:** {topic}")
            st.write("Step 1/4 — Retrieving relevant passages from vector DB...")

            from vedabase_notes_agent.retrieve.retriever import retrieve, format_context
            hits = retrieve(topic)
            st.write(f"Found **{len(hits)} passages** from: "
                     + ", ".join(sorted({f"NOI {h['verse_number']}" for h in hits})))

            st.write("Step 2/4 — Planning outline with Claude...")
            st.write("Step 3/4 — Drafting full notes with citations...")
            st.write("Step 4/4 — Verifying citations and sections...")

            from vedabase_notes_agent.agent.notes_agent import generate_notes
            notes = generate_notes(topic, audience, duration, style)

            from vedabase_notes_agent.export.export_markdown import export_notes
            saved_path = export_notes(notes, topic)

            st.session_state["generated_notes"] = notes
            st.session_state["saved_path"]       = str(saved_path)

            status.update(label="✅ Notes ready!", state="complete")

        except Exception as e:
            status.update(label="Generation failed", state="error")
            st.error(f"Error: {e}")
            st.stop()

# ── Display results ───────────────────────────────────────────────────────────

if "generated_notes" in st.session_state:
    notes      = st.session_state["generated_notes"]
    saved_path = st.session_state.get("saved_path", "")

    st.divider()

    # Action bar above the notes
    col_title, col_dl, col_clear = st.columns([4, 1, 1])
    with col_title:
        topic_label = st.session_state.get("last_topic", "Notes")
        st.subheader(f"📄 {topic_label}")
    with col_dl:
        st.download_button(
            "⬇ Download",
            data=notes,
            file_name=Path(saved_path).name if saved_path else "notes.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_clear:
        if st.button("✕ Clear", use_container_width=True):
            del st.session_state["generated_notes"]
            st.rerun()

    if saved_path:
        st.caption(f"Saved to: `{saved_path}`")

    # Render the notes as markdown in a scrollable container
    with st.container(border=True):
        st.markdown(notes)

# ── Sidebar: retrieved passages ───────────────────────────────────────────────

if "generated_notes" in st.session_state:
    with st.sidebar:
        st.markdown("### 📑 Verses Used")
        topic_label = st.session_state.get("last_topic", "")
        if topic_label:
            try:
                from vedabase_notes_agent.retrieve.retriever import retrieve
                hits = retrieve(topic_label)
                verses_used = sorted({f"NOI {h['verse_number'].capitalize()}" for h in hits})
                for v in verses_used:
                    st.markdown(f"- {v}")
            except Exception:
                pass
