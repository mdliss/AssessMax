"""Student detail page – evidence-rich profile for a single learner."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

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
from utils import (
    create_skill_chart,
    create_trend_chart,
    export_to_csv,
    export_to_pdf,
    format_skill_name,
    parse_uuid,
)

SAMPLE_STUDENTS = {
    "Emma Johnson": "550e8400-e29b-41d4-a716-446655440001",
    "Marcus Williams": "550e8400-e29b-41d4-a716-446655440002",
    "Sarah Chen": "550e8400-e29b-41d4-a716-446655440003",
    "Alicia Rivera": "550e8400-e29b-41d4-a716-446655440004",
}

STUDENT_BY_ID = {v: k for k, v in SAMPLE_STUDENTS.items()}


def show_student_detail() -> None:
    """Display detailed student assessment information."""

    default_id = st.session_state.get("selected_student_id", SAMPLE_STUDENTS["Emma Johnson"])

    with st.container():
        st.markdown("<div class='pulse-form drop-in'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1], gap="large")

        with col1:
            student_id_input = st.text_input(
                "Student UUID",
                value=default_id,
                help="Paste a Cognito-linked student UUID. Defaults to a rubric-compliant synthetic learner.",
            )

        with col2:
            if st.button("Refresh Records", use_container_width=True):
                fetch_latest_assessment.clear()  # type: ignore[attr-defined]
                fetch_assessment_history.clear()  # type: ignore[attr-defined]
                fetch_evidence.clear()  # type: ignore[attr-defined]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "Quick selections: "
        + " · ".join(f"{name}: `{uuid}`" for name, uuid in SAMPLE_STUDENTS.items())
    )

    if not student_id_input:
        render_empty_state("Awaiting Student Selection", "Enter a student UUID to stream assessments and evidence.")
        return

    try:
        student_uuid = parse_uuid(student_id_input)
    except ValueError as exc:
        st.error(f"Invalid Student ID: {exc}")
        return

    student_id_str = str(student_uuid)
    st.session_state["selected_student_id"] = student_id_str
    student_label = STUDENT_BY_ID.get(student_id_str, f"Student {student_id_str[:8].upper()}")

    with st.spinner("Streaming latest assessments and evidence..."):
        latest_assessment = fetch_latest_assessment(student_id_str)
        history = fetch_assessment_history(student_id_str)
        evidence = fetch_evidence(latest_assessment["assessment_id"]) if latest_assessment else {}

    if not latest_assessment:
        latest_assessment, history, evidence = _build_mock_student_payload(student_id_str, student_label)
        render_notification(
            "Synthesized learner trajectory using rubric-aligned synthetic data.",
            label="Demo Mode",
        )

    skills = latest_assessment.get("skills", [])
    top_skill = max(skills, key=lambda s: s["score"]) if skills else None
    avg_score = sum(skill["score"] for skill in skills) / len(skills) if skills else 0
    hero_badges = [
        HeroBadge(label="Student", value=student_label, tone="accent"),
        HeroBadge(
            label="Top Skill",
            value=format_skill_name(top_skill["skill"]) if top_skill else "N/A",
            tone="neutral",
        ),
        HeroBadge(
            label="Average Score",
            value=f"{avg_score:.1f}" if skills else "N/A",
            tone="neutral",
        ),
        HeroBadge(
            label="Last Assessed",
            value=latest_assessment.get("assessed_on", "N/A"),
            tone="neutral",
        ),
    ]
    render_page_header(
        "Student Deep Dive",
        f"Evidence-first profile for {student_label}.",
        badges=hero_badges,
    )

    show_latest_assessment(latest_assessment, student_label)
    st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)

    if evidence and evidence.get("evidence_spans"):
        show_evidence_section(evidence)
        st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)

    if history and history.get("assessments"):
        show_assessment_history(history, student_id_str, student_label)


@st.cache_data(ttl=300)
def fetch_latest_assessment(student_id: str) -> dict[str, Any]:
    """Fetch latest assessment for a student."""

    try:
        return AuthManager.api_get(f"/v1/assessments/{student_id}")
    except Exception:
        return {}


@st.cache_data(ttl=300)
def fetch_assessment_history(student_id: str, limit: int = 12) -> dict[str, Any]:
    """Fetch assessment history for a student."""

    try:
        return AuthManager.api_get(
            f"/v1/assessments/{student_id}/history",
            params={"limit": limit, "offset": 0},
        )
    except Exception:
        return {}


@st.cache_data(ttl=300)
def fetch_evidence(assessment_id: str) -> dict[str, Any]:
    """Fetch evidence for an assessment."""

    try:
        return AuthManager.api_get(f"/v1/evidence/{assessment_id}")
    except Exception:
        return {}


def show_latest_assessment(assessment: dict[str, Any], student_label: str) -> None:
    """Display latest assessment details."""

    render_section_header("Latest Assessment", "Most recent snapshot across the five skill domains.")

    render_metric_grid(
        [
            MetricDatum("Student", student_label, caption="Learner"),
            MetricDatum("Captured On", assessment.get("assessed_on", "N/A"), caption="Assessment date"),
            MetricDatum("Class ID", assessment.get("class_id", "N/A"), caption="Section"),
            MetricDatum("Model Version", assessment.get("model_version", "N/A"), caption="Pipeline build"),
        ],
        columns=4,
    )

    skills = assessment.get("skills", [])
    if not skills:
        render_empty_state("No skill scores available.", "Trigger the NLP pipeline to generate a fresh assessment.")
        return

    skill_data = {skill["skill"]: skill["score"] for skill in skills}

    left, right = st.columns([2, 1], gap="large")
    with left:
        fig = create_skill_chart(skill_data, title="Current Skill Signature")
        st.plotly_chart(fig, use_container_width=True, theme=None)

    with right:
        st.markdown("<div class='pulse-subheading'>Skill Focus</div>", unsafe_allow_html=True)
        for skill in skills:
            st.markdown(
                f"""
                <div class="pulse-card drop-in">
                    <span class="pulse-subheading">{format_skill_name(skill['skill'])}</span>
                    <div class="pulse-metric-value">{skill['score']:.1f}</div>
                    <div class="pulse-pill">Confidence: {skill['confidence']:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_evidence_section(evidence: dict[str, Any]) -> None:
    """Display evidence spans for the assessment."""

    render_section_header("Evidence Highlights", "Ground each score with transcript and artifact citations.")
    evidence_spans = evidence.get("evidence_spans", [])
    if not evidence_spans:
        render_empty_state("No evidence data available.", "Upload annotated transcripts or artifacts to populate evidence.")
        return

    evidence_by_skill: dict[str, list[dict[str, Any]]] = {}
    for span in evidence_spans:
        evidence_by_skill.setdefault(span.get("skill", "unknown"), []).append(span)

    for skill, spans in evidence_by_skill.items():
        st.markdown(
            f"<div class='pulse-subheading'>{format_skill_name(skill)}</div>",
            unsafe_allow_html=True,
        )
        for span_idx, span in enumerate(spans, start=1):
            st.markdown(
                f"""
                <div class="pulse-card drop-in">
                    <div class="pulse-pill">Evidence {span_idx}</div>
                    <p><em>{span.get('span_text', 'N/A')}</em></p>
                    <div class="pill-group">
                        <span class="pulse-badge">{span.get('span_location', 'Unknown')}</span>
                        {f"<span class='pulse-badge'>Contribution · {span.get('score_contribution', 0):.2f}</span>" if span.get('score_contribution') is not None else ''}
                    </div>
                    {f"<div class='pulse-subheading'>Rationale</div><p>{span.get('rationale')}</p>" if span.get('rationale') else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_assessment_history(history: dict[str, Any], student_id: str, student_label: str) -> None:
    """Display assessment history and exports."""

    render_section_header("Progression Timeline", "Compare individual movement across review windows.")
    assessments = history.get("assessments", [])
    if not assessments:
        render_empty_state("Not enough data for trends.", "Ingest additional transcripts to extend the timeline.")
        return

    trend_rows = []
    for assessment in assessments:
        row = {"assessed_on": assessment["assessed_on"]}
        for skill in assessment.get("skills", []):
            row[skill["skill"]] = skill["score"]
        trend_rows.append(row)

    df = pd.DataFrame(trend_rows).sort_values("assessed_on")
    df["assessed_on"] = pd.to_datetime(df["assessed_on"])

    skills = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]
    tabs = st.tabs([format_skill_name(skill) for skill in skills])
    for tab, skill in zip(tabs, skills):
        with tab:
            if skill in df.columns:
                fig = create_trend_chart(df, skill, title=f"{format_skill_name(skill)} Over Time")
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.info("No data available for this skill.")

    render_section_header("Assessment Ledger", "Tabular export of every captured assessment event.")
    ledger_rows = []
    for assessment in assessments:
        row = {
            "Assessment ID": str(assessment["assessment_id"]),
            "Recorded": assessment["assessed_on"],
            "Class": assessment.get("class_id", "N/A"),
        }
        for skill in assessment.get("skills", []):
            row[format_skill_name(skill["skill"])] = f"{skill['score']:.1f}"
        ledger_rows.append(row)

    ledger_df = pd.DataFrame(ledger_rows)
    st.dataframe(
        ledger_df,
        use_container_width=True,
        hide_index=True,
        height=360,
    )

    st.markdown("#### Export")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = export_to_csv(ledger_rows)
        st.download_button(
            label="CSV Export",
            data=csv_data,
            file_name=f"student_{student_id}_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        pdf_data = export_to_pdf(
            title="Student Assessment History",
            data=ledger_rows,
            student_name=student_label,
        )
        st.download_button(
            label="PDF Snapshot",
            data=pdf_data,
            file_name=f"student_{student_id}_history.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _build_mock_student_payload(student_id: str, student_label: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Construct mock data for a student when the API is unavailable."""

    random.seed(hash(student_id) % 1_000_003)
    base_date = date.today()
    skill_list = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]

    history_assessments = []
    for weeks_ago in range(12):
        assessed_on = base_date - timedelta(days=7 * weeks_ago)
        skills = []
        for skill in skill_list:
            score = random.uniform(60, 95) + weeks_ago * random.uniform(-0.6, 0.6)
            skills.append(
                {
                    "skill": skill,
                    "score": round(max(55, min(score, 98)), 1),
                    "confidence": round(random.uniform(0.62, 0.94), 2),
                }
            )

        history_assessments.append(
            {
                "assessment_id": uuid4(),
                "student_id": UUID(student_id),
                "class_id": f"MS-7{random.choice(['A', 'B'])}",
                "assessed_on": assessed_on.isoformat(),
                "skills": skills,
            }
        )

    history_assessments.sort(key=lambda x: x["assessed_on"], reverse=True)
    latest = history_assessments[0]

    evidence_spans = []
    for skill in skill_list:
        for idx in range(2):
            evidence_spans.append(
                {
                    "evidence_id": str(uuid4()),
                    "skill": skill,
                    "span_text": f"{student_label} demonstrated {format_skill_name(skill).lower()} during project stand-up {idx + 1}.",
                    "span_location": f"Transcript line {random.randint(20, 120)}",
                    "rationale": f"Highlights clear indicators of {format_skill_name(skill).lower()}.",
                    "score_contribution": round(random.uniform(0.35, 0.85), 2),
                }
            )

    latest_payload = {
        "assessment_id": latest["assessment_id"],
        "student_id": latest["student_id"],
        "class_id": latest["class_id"],
        "assessed_on": latest["assessed_on"],
        "model_version": "1.0.0-sim",
        "skills": latest["skills"],
    }

    history_payload = {
        "student_id": latest["student_id"],
        "assessments": history_assessments,
        "total": len(history_assessments),
    }

    evidence_payload = {
        "assessment_id": latest["assessment_id"],
        "evidence_spans": evidence_spans,
        "total": len(evidence_spans),
    }

    return latest_payload, history_payload, evidence_payload
