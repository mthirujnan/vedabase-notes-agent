"""
jobs.py
-------
Background job queue for note generation.

Beginner tip — why a job queue?
  Generating notes takes 20-60 seconds (multiple Claude API calls).
  If we block the UI while waiting, the user is stuck on one page.
  Instead, we:
    1. Start the work in a background thread
    2. Write progress/result to a JSON file on disk
    3. Let the user browse freely
    4. Every page sidebar checks the job files and shows status

  Think of it like ordering food at a restaurant — you get a number,
  sit down, and they call you when it's ready. You don't stand at
  the counter the whole time.

Job lifecycle:
  "queued" → "running" → "done"
                       → "error"
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path

from vedabase_notes_agent.config import OUT_DIR

# Jobs are stored as small JSON files in data/outputs/jobs/
JOBS_DIR = OUT_DIR / "jobs"


# ── Start a job ───────────────────────────────────────────────────────────────

def start_job(
    topic:    str,
    audience: str,
    duration: int,
    style:    str,
) -> str:
    """
    Launch note generation in a background thread.
    Returns a short job_id string (e.g. "a3f9b2c1").
    """
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]

    # Write the initial job record to disk
    _write_job(job_id, {
        "job_id":      job_id,
        "topic":       topic,
        "audience":    audience,
        "duration":    duration,
        "style":       style,
        "status":      "running",
        "created_at":  datetime.now().isoformat(),
        "completed_at": None,
        "result_path": None,
        "error":       None,
    })

    # Start background thread (daemon=True means it won't block app exit)
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, topic, audience, duration, style),
        daemon=True,
    )
    thread.start()

    return job_id


# ── Background worker ─────────────────────────────────────────────────────────

def _run_job(job_id: str, topic: str, audience: str, duration: int, style: str):
    """
    Runs in a background thread.
    Generates the notes and updates the job file when done.
    """
    try:
        from vedabase_notes_agent.agent.notes_agent import generate_notes
        from vedabase_notes_agent.export.export_markdown import export_notes

        notes      = generate_notes(topic, audience, duration, style)
        saved_path = export_notes(notes, topic)

        _update_job(job_id, {
            "status":       "done",
            "completed_at": datetime.now().isoformat(),
            "result_path":  str(saved_path),
        })

    except Exception as exc:
        _update_job(job_id, {
            "status": "error",
            "error":  str(exc),
        })


# ── Read jobs ─────────────────────────────────────────────────────────────────

def get_all_jobs() -> list[dict]:
    """Return all jobs, newest first."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []
    for f in JOBS_DIR.glob("*.json"):
        try:
            jobs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def get_job(job_id: str) -> dict | None:
    """Return a single job by ID, or None if not found."""
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        return json.loads(job_file.read_text(encoding="utf-8"))
    return None


def clear_job(job_id: str):
    """Delete a completed/errored job record."""
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        job_file.unlink()


def has_running_jobs() -> bool:
    """Quick check — is anything still generating?"""
    return any(j["status"] == "running" for j in get_all_jobs())


# ── Write helpers ─────────────────────────────────────────────────────────────

def _write_job(job_id: str, data: dict):
    job_file = JOBS_DIR / f"{job_id}.json"
    job_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_job(job_id: str, updates: dict):
    job = get_job(job_id) or {}
    job.update(updates)
    _write_job(job_id, job)
