"""
ui_jobs.py
----------
Shared sidebar widget that shows background job status on every page.

Import and call show_jobs_sidebar() at the bottom of any page's sidebar section.
"""

from __future__ import annotations

import streamlit as st
from vedabase_notes_agent.jobs import get_all_jobs, clear_job


def show_jobs_sidebar():
    """
    Render a 'Background Jobs' section in the sidebar.

    - Shows running jobs with a spinner
    - Shows completed jobs with a link to the notes
    - Shows failed jobs with the error
    - Auto-refreshes every 5 seconds while a job is running
    """
    jobs = get_all_jobs()
    if not jobs:
        return  # nothing to show

    st.sidebar.divider()
    st.sidebar.markdown("### 🔄 Background Jobs")

    any_running = False

    for job in jobs[:5]:  # show latest 5 jobs
        status     = job.get("status", "unknown")
        topic      = job.get("topic", "Unknown topic")
        job_id     = job.get("job_id", "")
        short_topic = topic[:30] + ("..." if len(topic) > 30 else "")

        if status == "running":
            any_running = True
            st.sidebar.markdown(f"⏳ **Generating...**\n\n*{short_topic}*")

        elif status == "done":
            result_path = job.get("result_path", "")
            col1, col2 = st.sidebar.columns([3, 1])
            col1.markdown(f"✅ **Done**\n\n*{short_topic}*")
            if col2.button("✕", key=f"clear_{job_id}", help="Dismiss"):
                clear_job(job_id)
                st.rerun()
            if result_path:
                try:
                    from pathlib import Path
                    content = Path(result_path).read_text(encoding="utf-8")
                    st.sidebar.download_button(
                        "⬇ Download",
                        data=content,
                        file_name=Path(result_path).name,
                        mime="text/markdown",
                        key=f"dl_{job_id}",
                        use_container_width=True,
                    )
                except Exception:
                    pass

        elif status == "error":
            col1, col2 = st.sidebar.columns([3, 1])
            col1.markdown(f"❌ **Failed**\n\n*{short_topic}*")
            if col2.button("✕", key=f"clear_err_{job_id}", help="Dismiss"):
                clear_job(job_id)
                st.rerun()
            with st.sidebar.expander("See error"):
                st.error(job.get("error", "Unknown error"))

    # Auto-refresh while a job is running so status updates appear
    if any_running:
        st.sidebar.caption("Refreshing every 5s...")
        import time
        time.sleep(5)
        st.rerun()
