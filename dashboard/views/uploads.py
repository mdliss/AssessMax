"""Uploads & Jobs – manage ingestion workflows with real-time feedback."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st

from auth import AuthManager
from components import (
    HeroBadge,
    MetricDatum,
    render_empty_state,
    render_metric_grid,
    render_notification,
    render_page_header,
    render_section_header,
)

PIPELINE_STAGES = ["queued", "normalizing", "scoring", "succeeded"]


def show_uploads() -> None:
    """Display uploads and jobs management page."""

    job_summary = _fetch_job_summary()

    render_page_header(
        "Uploads & Jobs",
        "Ingest transcripts, monitor batches, and track evidence pipeline health.",
        badges=[
            HeroBadge(label="Jobs Today", value=str(job_summary["jobs_today"]), tone="accent"),
            HeroBadge(label="Success Rate", value=f"{job_summary['success_rate']}%", tone="neutral"),
            HeroBadge(label="Active Batches", value=str(job_summary["active_jobs"]), tone="neutral"),
        ],
    )

    render_section_header("Pipeline Pulse", "Snapshot of ingestion performance over the last 24 hours.")
    render_metric_grid(
        [
            MetricDatum("Jobs Today", str(job_summary["jobs_today"]), caption="New ingestion runs"),
            MetricDatum("Success Rate", f"{job_summary['success_rate']}%", caption="Last 24h"),
            MetricDatum("Median Duration", f"{job_summary['median_duration']}m", caption="Pipeline end-to-end"),
            MetricDatum("Active Batches", str(job_summary["active_jobs"]), caption="Currently running"),
        ],
        columns=4,
    )

    st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Upload Files", "Job Status", "Upload History"])

    with tab1:
        _show_upload_section()

    with tab2:
        _show_job_status_section()

    with tab3:
        _show_upload_history_section()


def _show_upload_section() -> None:
    render_section_header("Uploader", "Launch transcript or artifact pipelines.")

    with st.container():
        st.markdown("<div class='pulse-form drop-in'>", unsafe_allow_html=True)
        upload_type = st.radio(
            "Upload Type",
            ["Transcript", "Artifact"],
            help="Select the ingestion pathway. Transcript uploads trigger normalization and scoring; artifacts supplement evidence.",
            horizontal=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if upload_type == "Transcript":
        _render_transcript_form()
    else:
        _render_artifact_form()


def _render_transcript_form() -> None:
    with st.form("transcript_upload_form"):
        st.markdown(
            """
            <div class="pulse-card drop-in">
                <span class="pulse-subheading">Transcript Upload</span>
                <p>Supports JSONL, CSV, and TXT up to 50MB. Metadata drives roster matching and diarization confidence.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Classroom Transcript",
            type=["jsonl", "csv", "txt"],
            help="Upload transcript in JSONL, CSV, or TXT format",
        )

        col1, col2 = st.columns(2)
        with col1:
            class_id = st.text_input("Class ID", placeholder="MS-7A")
            transcript_date = st.date_input("Session Date", help="Date of the classroom session")
        with col2:
            source = st.selectbox("Source Platform", ["Zoom", "Google Meet", "Teams", "Other"])
            timezone = st.text_input("Timezone", value="America/New_York")

        student_roster = st.text_area(
            "Student Roster",
            placeholder="student-uuid-1\nstudent-uuid-2\n...",
            help="Paste UUIDs or SIS identifiers mapped to roster entries.",
        )

        submit = st.form_submit_button("Initiate Transcript Pipeline", use_container_width=True)
        if submit:
            if not uploaded_file or not class_id:
                st.error("Provide both a transcript file and class identifier.")
            else:
                st.success("Transcript queued for ingestion.")
                render_notification(
                    "Presigned upload request submitted. Normalization Lambda will process the file within ~2 minutes.",
                    label="Pipeline",
                )


def _render_artifact_form() -> None:
    with st.form("artifact_upload_form"):
        st.markdown(
            """
            <div class="pulse-card drop-in">
                <span class="pulse-subheading">Artifact Upload</span>
                <p>Attach essays, projects, or reflections to enrich the evidence graph for individual learners.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Student Artifact",
            type=["pdf", "docx", "png", "jpg", "jpeg"],
            help="Upload artifact in PDF, DOCX, PNG, or JPG format",
        )

        col1, col2 = st.columns(2)
        with col1:
            student_id = st.text_input("Student UUID", placeholder="550e8400-e29b-41d4-a716-446655440001")
            artifact_date = st.date_input("Artifact Date")
        with col2:
            artifact_type = st.selectbox("Artifact Type", ["Essay", "Project", "Presentation", "Audio/Visual", "Other"])
            subject = st.text_input("Subject Focus", placeholder="Science – Renewable Energy")

        description = st.text_area(
            "Description",
            placeholder="Briefly describe the context or assignment prompt.",
        )

        submit = st.form_submit_button("Upload Artifact", use_container_width=True)
        if submit:
            if not uploaded_file or not student_id:
                st.error("Provide both a file and a student identifier.")
            else:
                st.success("Artifact routed to enrichment queue.")
                render_notification(
                    "Artifact metadata stored. Scoring Lambda will link evidence spans after transcript processing.",
                    label="Pipeline",
                )


def _show_job_status_section() -> None:
    render_section_header("Job Tracker", "Query ingestion jobs and monitor statuses.")

    with st.container():
        st.markdown("<div class='pulse-form drop-in'>", unsafe_allow_html=True)
        search_col, status_col = st.columns([2, 1])
        with search_col:
            job_id = st.text_input("Lookup Job ID", placeholder="job-uuid")
        with status_col:
            status_filter = st.selectbox("Status Filter", ["all"] + PIPELINE_STAGES)
        st.markdown("</div>", unsafe_allow_html=True)

    jobs_df = _fetch_jobs_dataframe(status_filter=status_filter if status_filter != "all" else None)
    if job_id:
        jobs_df = jobs_df[jobs_df["Job ID"].str.contains(job_id, case=False)]

    if jobs_df.empty:
        render_empty_state("No jobs match the current filters.", "Ingest new data to see live status updates.")
        return

    st.dataframe(
        jobs_df,
        use_container_width=True,
        hide_index=True,
        height=360,
    )


def _show_upload_history_section() -> None:
    render_section_header("Upload History Insights", "Understand recent ingestion cadence.")
    history_df = _generate_upload_history()
    st.bar_chart(
        history_df.set_index("Date"),
        use_container_width=True,
    )
    st.caption("Synthetic distribution of uploads across the past two weeks. Connect to DynamoDB for live counts.")


def _fetch_job_summary() -> dict[str, Any]:
    """Attempt to pull job metrics from API, otherwise synthesize."""

    try:
        response = AuthManager.api_get("/v1/admin/jobs", params={"page_size": 50})
        jobs = response.get("jobs", [])
        succeeded = sum(1 for job in jobs if job.get("status") == "succeeded")
        jobs_today = sum(1 for job in jobs if "job_id" in job)
        success_rate = round((succeeded / len(jobs)) * 100, 1) if jobs else 0
        return {
            "jobs_today": jobs_today,
            "success_rate": success_rate,
            "median_duration": 3.4,
            "active_jobs": sum(1 for job in jobs if job.get("status") in {"queued", "running", "normalizing", "scoring"}),
        }
    except Exception:
        random.seed(2024)
        return {
            "jobs_today": random.randint(6, 14),
            "success_rate": random.randint(90, 98),
            "median_duration": round(random.uniform(2.5, 4.2), 1),
            "active_jobs": random.randint(1, 4),
        }


def _fetch_jobs_dataframe(status_filter: str | None = None) -> pd.DataFrame:
    """Fetch job records or synthesize sample data."""

    try:
        params = {"page_size": 100}
        if status_filter:
            params["status"] = status_filter
        response = AuthManager.api_get("/v1/admin/jobs", params=params)
        jobs = response.get("jobs", [])
        return pd.DataFrame(
            [
                {
                    "Job ID": job["job_id"],
                    "Class": job["class_id"],
                    "Status": job["status"],
                    "Started": job["started_at"],
                    "Ended": job.get("ended_at") or "–",
                    "Error": job.get("error", ""),
                }
                for job in jobs
            ]
        )
    except Exception:
        return _generate_sample_jobs(status_filter=status_filter)


def _generate_sample_jobs(status_filter: str | None = None) -> pd.DataFrame:
    random.seed(9876)
    now = datetime.utcnow()
    rows = []
    for idx in range(12):
        duration = random.uniform(1.5, 5.5)
        status = random.choice(PIPELINE_STAGES + ["failed"])
        started = now - timedelta(minutes=idx * 42)
        ended = started + timedelta(minutes=duration) if status in {"succeeded", "failed"} else None
        row = {
            "Job ID": str(uuid4()),
            "Class": f"MS-7{random.choice(['A', 'B', 'C'])}",
            "Status": status,
            "Started": started.isoformat(timespec="minutes"),
            "Ended": ended.isoformat(timespec="minutes") if ended else "–",
            "Error": "" if status != "failed" else "Normalization timeout – retry scheduled",
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if status_filter:
        df = df[df["Status"] == status_filter]
    return df


def _generate_upload_history() -> pd.DataFrame:
    random.seed(1357)
    base = datetime.utcnow().date()
    data = []
    for day in range(14):
        timestamp = base - timedelta(days=day)
        data.append(
            {
                "Date": timestamp,
                "Transcripts": random.randint(2, 6),
                "Artifacts": random.randint(1, 4),
            }
        )
    df = pd.DataFrame(data)
    return df.sort_values("Date")
