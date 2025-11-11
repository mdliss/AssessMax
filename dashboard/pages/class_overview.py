"""Class Overview page - Display class-level metrics and student summaries."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st

from auth import AuthManager
from components import MetricDatum, render_logo_badge, render_metric_grid, render_notification
from utils import create_skill_chart, export_to_csv, export_to_pdf, format_skill_name


def show_class_overview() -> None:
    """Display class overview with metrics and student summaries."""

    render_logo_badge("Class Pulse", "Monitor cohort performance in real time")

    with st.form("class_filter_form"):
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            class_id = st.text_input(
                "Class Identifier",
                value="MS-7A",
                placeholder="e.g., MS-7A",
                label_visibility="visible",
                help="Enter the roster identifier or cohort slug.",
            )

        with col2:
            refresh = st.form_submit_button("Refresh Pulse", use_container_width=True)

        with col3:
            if st.form_submit_button("Clear Cache", use_container_width=True):
                st.cache_data.clear()
                st.experimental_rerun()

    if not class_id:
        st.info("ℹ️ Provide a class identifier to render analytics.")
        return

    try:
        if refresh:
            fetch_class_dashboard.clear()  # type: ignore[attr-defined]

        with st.spinner("Synthesizing class telemetry..."):
            data = fetch_class_dashboard(class_id)

        if not data:
            data = _build_mock_class_dashboard(class_id)
            render_notification(
                "Live API unavailable. Showing PulseMax synthetic dataset aligned to rubric expectations.",
                label="Demo Mode",
            )

        metrics_block = data.get("metrics", {})
        students = data.get("students", [])

        show_class_metrics(metrics_block)
        st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)
        show_class_averages(metrics_block)
        st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)
        show_student_summaries(students, class_id)

    except Exception as exc:  # pragma: no cover - UI path
        st.error(f"❌ Error loading class data: {exc}")
        st.info("💡 Ensure the backend API is reachable or rely on mock data.")


@st.cache_data(ttl=300)
def fetch_class_dashboard(class_id: str) -> dict[str, Any]:
    """Fetch class dashboard data from API."""

    try:
        return AuthManager.api_get(f"/v1/classes/{class_id}/dashboard")
    except Exception:
        return {}


def show_class_metrics(metrics: dict[str, Any]) -> None:
    """Display class-level metrics."""

    student_count = metrics.get("student_count", 0)
    total_assessments = metrics.get("total_assessments", 0)
    avg_per_student = total_assessments / student_count if student_count else 0
    date_range = metrics.get("date_range")

    if date_range and len(date_range) == 2:
        start, end = date_range
        days = (end - start).days or 1
        coverage = f"{start:%b %d} → {end:%b %d}"
    else:
        days = 0
        coverage = "N/A"

    render_metric_grid(
        [
            MetricDatum("Active Students", f"{student_count}", caption="Roster size"),
            MetricDatum(
                "Assessments Captured",
                f"{total_assessments}",
                caption="Total submissions",
            ),
            MetricDatum(
                "Avg / Student",
                f"{avg_per_student:.1f}",
                caption="Assessments-per-student",
            ),
            MetricDatum(
                "Coverage Window",
                coverage,
                caption=f"{days} days of signals",
            ),
        ],
        columns=4,
    )


def show_class_averages(metrics: dict[str, Any]) -> None:
    """Display class average skill scores."""

    class_averages = metrics.get("class_averages", {})

    if not class_averages:
        st.info("No skill score data available")
        return

    left, right = st.columns([2, 1], gap="large")
    with left:
        fig = create_skill_chart(class_averages, title="Class Skill Signature")
        st.plotly_chart(fig, use_container_width=True, theme=None)

    with right:
        st.markdown("#### Signal Strength")
        for skill, score in sorted(class_averages.items(), key=lambda x: -x[1]):
            st.markdown(
                f"<div class='pulse-card drop-in'>"
                f"<span class='pulse-subheading'>{format_skill_name(skill)}</span>"
                f"<div class='pulse-metric-value'>{score:.1f}</div>"
                "<div class='pulse-pill'>Score / 100</div>"
                "</div>",
                unsafe_allow_html=True,
            )


def show_student_summaries(students: list[dict[str, Any]], class_id: str) -> None:
    """Display student summary table."""

    if not students:
        st.info("No student data available")
        return

    table_data = []
    for student in students:
        latest = student.get("latest_assessment")
        avg_scores = student.get("average_scores", {})
        overall_avg = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0

        row = {
            "Student": student.get("name") or "Unknown",
            "Student ID": str(student["student_id"]),
            "Assessments": student.get("assessment_count", 0),
            "Last Assessed": latest["assessed_on"] if latest else "N/A",
            "Overall Avg": round(overall_avg, 1),
            **{
                format_skill_name(skill): round(avg_scores.get(skill, 0.0), 1)
                for skill in ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]
            },
        }
        table_data.append(row)

    df = pd.DataFrame(table_data)

    st.markdown("#### Roster Snapshot")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    st.markdown("#### Export Pulse")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = export_to_csv(table_data)
        st.download_button(
            label="📄 CSV Export",
            data=csv_data,
            file_name=f"class_{class_id}_overview.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        pdf_data = export_to_pdf(
            title=f"Class Overview · {class_id}",
            data=table_data,
            class_id=class_id,
        )
        st.download_button(
            label="📑 PDF Snapshot",
            data=pdf_data,
            file_name=f"class_{class_id}_overview.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _build_mock_class_dashboard(class_id: str) -> dict[str, Any]:
    """Construct rubric-aligned synthetic data for offline mode."""

    random.seed(hash(class_id) % 1_000_000)
    students = [
        {
            "student_id": uuid4(),
            "name": name,
            "assessment_count": random.randint(6, 12),
            "latest_assessment": {
                "assessment_id": uuid4(),
                "assessed_on": (date.today() - timedelta(days=random.randint(0, 5))).isoformat(),
                "class_id": class_id,
                "skills": [
                    {"skill": skill, "score": random.uniform(65, 95), "confidence": round(random.uniform(0.6, 0.95), 2)}
                    for skill in ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]
                ],
            },
        }
        for name in ["Emma Johnson", "Marcus Williams", "Sarah Chen", "Alicia Rivera", "Omar Patel", "Liam Cooper"]
    ]

    for student in students:
        student["average_scores"] = {
            score["skill"]: score["score"] + random.uniform(-5, 5) for score in student["latest_assessment"]["skills"]
        }

    total_assessments = sum(s["assessment_count"] for s in students)
    class_averages: dict[str, float] = {}
    for student in students:
        for skill, value in student["average_scores"].items():
            class_averages.setdefault(skill, 0.0)
            class_averages[skill] += value
    class_averages = {
        skill: round(value / len(students), 1) for skill, value in class_averages.items()
    }

    metrics = {
        "class_id": class_id,
        "student_count": len(students),
        "total_assessments": total_assessments,
        "date_range": (date.today() - timedelta(days=42), date.today()),
        "class_averages": class_averages,
    }

    return {
        "class_id": class_id,
        "metrics": metrics,
        "students": students,
    }
