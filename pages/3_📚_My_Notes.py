"""
My Notes page — browse and read all previously generated notes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from vedabase_notes_agent.config import OUT_DIR

st.set_page_config(page_title="My Notes — Vedabase", page_icon="📚", layout="wide")
st.title("📚 My Notes")
st.markdown("All previously generated notes saved in `data/outputs/`.")
st.divider()

# ── List saved note files ─────────────────────────────────────────────────────

OUT_DIR.mkdir(parents=True, exist_ok=True)
note_files = sorted(OUT_DIR.glob("*.md"), reverse=True)  # newest first

if not note_files:
    st.info(
        "No notes yet. Head to **📝 Generate Notes** to create your first set!",
        icon="💡",
    )
    st.stop()

# ── Two-column layout: file list on left, content on right ────────────────────

col_list, col_content = st.columns([1, 3])

with col_list:
    st.markdown("#### Saved Notes")
    st.caption(f"{len(note_files)} file(s)")

    # Build display labels: strip prefix "notes_" and suffix "_YYYY-MM-DD.md"
    def pretty_name(p: Path) -> str:
        name = p.stem  # removes .md
        name = name.removeprefix("notes_")
        # split off date suffix (last 10 chars if it looks like a date)
        if len(name) > 11 and name[-10] == "_" and name[-9:4:3].isdigit():
            date_part = name[-10:].replace("_", "")
            topic_part = name[:-11].replace("_", " ").title()
            return f"{topic_part}\n{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
        return name.replace("_", " ").title()

    selected_file = None
    for f in note_files:
        label = pretty_name(f)
        # Show just the first line as the button label
        first_line = label.split("\n")[0]
        date_line  = label.split("\n")[1] if "\n" in label else f.stem[-10:]
        if st.button(
            first_line,
            key=str(f),
            help=f"Date: {date_line}",
            use_container_width=True,
        ):
            st.session_state["viewing_note"] = str(f)

# ── Content panel ─────────────────────────────────────────────────────────────

with col_content:
    # Auto-select first file if nothing selected yet
    if "viewing_note" not in st.session_state and note_files:
        st.session_state["viewing_note"] = str(note_files[0])

    viewing = st.session_state.get("viewing_note")

    if viewing:
        note_path = Path(viewing)
        if note_path.exists():
            content = note_path.read_text(encoding="utf-8")

            # Header bar
            hcol1, hcol2, hcol3 = st.columns([4, 1, 1])
            with hcol1:
                st.markdown(f"#### {pretty_name(note_path).split(chr(10))[0]}")
                st.caption(f"`{note_path.name}`")
            with hcol2:
                st.download_button(
                    "⬇ Download",
                    data=content,
                    file_name=note_path.name,
                    mime="text/markdown",
                    use_container_width=True,
                )
            with hcol3:
                if st.button("🗑 Delete", use_container_width=True, type="secondary"):
                    note_path.unlink()
                    del st.session_state["viewing_note"]
                    st.rerun()

            st.divider()

            # Render note as markdown
            with st.container(border=True):
                st.markdown(content)
        else:
            st.warning("File no longer exists.")
            del st.session_state["viewing_note"]

# ── Background jobs sidebar ─────────────────────────────────────────────────
from vedabase_notes_agent.ui_jobs import show_jobs_sidebar
show_jobs_sidebar()
