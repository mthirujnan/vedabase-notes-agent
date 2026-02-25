"""
Generate Notes page — async version.

Clicking Generate starts a background job and immediately returns
control to the user. They can navigate away freely.
The sidebar on every page shows live job status.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from vedabase_notes_agent.config import CLAUDE_API_KEY

st.set_page_config(page_title="Generate Notes — Vedabase", page_icon="📝", layout="wide")
st.title("📝 Generate Notes")
st.markdown(
    "Describe your topic and hit **Generate**. "
    "Notes build in the background — you can browse other pages while you wait. "
    "Watch the sidebar for completion."
)
st.divider()

# ── Guard: pipeline ready? ────────────────────────────────────────────────────

try:
    from vedabase_notes_agent.index.vector_store import collection_size
    pipeline_ready = collection_size() > 0
except Exception:
    pipeline_ready = False

if not pipeline_ready:
    st.warning("The vector database is empty. Complete the **⚙️ Pipeline** steps first.", icon="⚠️")
    st.stop()

if not CLAUDE_API_KEY:
    st.error("CLAUDE_API_KEY is not set. Add it to your `.env` file.", icon="🔑")
    st.stop()

# ── Input form ────────────────────────────────────────────────────────────────

with st.form("notes_form"):
    st.subheader("What would you like notes on?")

    topic = st.text_input(
        "Topic *",
        placeholder="e.g. controlling the six urges, qualities of a Vaishnava, Vrindavana...",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        audience = st.text_input("Audience", value="general devotees")
    with col2:
        duration = st.slider("Duration (minutes)", 15, 120, 60, step=15)
    with col3:
        style = st.radio("Style", ["class", "discourse"])

    submitted = st.form_submit_button(
        "✨ Generate in Background",
        type="primary",
        use_container_width=True,
    )

# ── On submit: start background job ──────────────────────────────────────────

if submitted:
    if not topic.strip():
        st.error("Please enter a topic.")
    else:
        from vedabase_notes_agent.jobs import start_job
        job_id = start_job(topic.strip(), audience, duration, style)

        st.success(
            f"**Generating in the background!**  Job ID: `{job_id}`\n\n"
            "You can navigate to any page — the sidebar will show when notes are ready.",
            icon="🚀",
        )
        st.info(
            "**What the agent is doing:**\n"
            "1. Retrieving relevant NOI passages from vector DB\n"
            "2. Planning an outline with Claude\n"
            "3. Drafting notes with NOI citations, stories & supplemental Prabhupada references\n"
            "4. Verifying all citations and sections\n"
            "5. Saving to `data/outputs/`",
            icon="🤖",
        )

# ── Recent jobs on this page ──────────────────────────────────────────────────

st.divider()
st.subheader("Recent Jobs")

from vedabase_notes_agent.jobs import get_all_jobs, clear_job

jobs = get_all_jobs()
if not jobs:
    st.caption("No jobs yet. Generate your first notes above!")
else:
    for job in jobs[:10]:
        status     = job["status"]
        topic_text = job.get("topic", "")
        job_id     = job["job_id"]
        icon = {"running": "⏳", "done": "✅", "error": "❌"}.get(status, "❓")

        with st.container(border=True):
            col_info, col_action = st.columns([5, 1])

            with col_info:
                st.markdown(f"{icon} **{topic_text}**")
                st.caption(
                    f"Style: {job.get('style')} · "
                    f"Audience: {job.get('audience')} · "
                    f"Duration: {job.get('duration')} min · "
                    f"ID: `{job_id}`"
                )

                if status == "running":
                    st.progress(0.0, text="Generating... (20-60 seconds)")

                elif status == "done":
                    result_path = job.get("result_path", "")
                    st.caption(f"Saved: `{result_path}`")
                    if result_path and Path(result_path).exists():
                        with st.expander("Preview notes"):
                            st.markdown(Path(result_path).read_text(encoding="utf-8"))

                elif status == "error":
                    st.error(job.get("error", "Unknown error"))

            with col_action:
                st.write("")
                if status != "running":
                    if st.button("✕ Clear", key=f"clear_{job_id}", use_container_width=True):
                        clear_job(job_id)
                        st.rerun()
                if status == "done":
                    result_path = job.get("result_path", "")
                    if result_path and Path(result_path).exists():
                        st.download_button(
                            "⬇ Download",
                            data=Path(result_path).read_text(encoding="utf-8"),
                            file_name=Path(result_path).name,
                            mime="text/markdown",
                            key=f"dl_{job_id}",
                            use_container_width=True,
                        )

# ── Sidebar jobs widget ───────────────────────────────────────────────────────

from vedabase_notes_agent.ui_jobs import show_jobs_sidebar
show_jobs_sidebar()
