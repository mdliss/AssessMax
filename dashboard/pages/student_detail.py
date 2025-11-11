"""Student Detail page - Display individual student assessment details"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from auth import AuthManager
from utils import (
    create_skill_chart,
    create_trend_chart,
    export_to_csv,
    export_to_pdf,
    format_skill_name,
    parse_uuid,
)


def show_student_detail() -> None:
    """Display detailed student assessment information"""

    st.title("👤 Student Detail")
    st.markdown("View individual student assessment history and skill progression")

    # Student ID input
    col1, col2 = st.columns([2, 1])

    with col1:
        student_id_input = st.text_input(
            "Enter Student ID (UUID)",
            help="Enter the student's UUID to view their details",
            label_visibility="visible",
        )

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not student_id_input:
        st.info("ℹ️ Please enter a student ID to view data")
        return

    try:
        student_id = parse_uuid(student_id_input)
    except ValueError as e:
        st.error(f"❌ Invalid Student ID: {str(e)}")
        return

    # Fetch student data
    try:
        with st.spinner("Loading student data..."):
            latest_assessment = fetch_latest_assessment(str(student_id))
            history = fetch_assessment_history(str(student_id))
            evidence = None
            if latest_assessment:
                evidence = fetch_evidence(latest_assessment["assessment_id"])

        if not latest_assessment:
            st.warning(f"⚠️ No assessments found for student: {student_id}")
            return

        # Display latest assessment
        show_latest_assessment(latest_assessment)

        st.divider()

        # Display evidence
        if evidence:
            show_evidence_section(evidence)
            st.divider()

        # Display assessment history
        if history and history.get("assessments"):
            show_assessment_history(history, str(student_id))

    except Exception as e:
        st.error(f"❌ Error loading student data: {str(e)}")
        st.info("💡 Make sure the backend API is running and the student ID is valid")


@st.cache_data(ttl=300)
def fetch_latest_assessment(student_id: str) -> dict[str, Any]:
    """Fetch latest assessment for a student"""
    try:
        return AuthManager.api_get(f"/v1/assessments/{student_id}")
    except Exception as e:
        st.error(f"Failed to fetch latest assessment: {str(e)}")
        return {}


@st.cache_data(ttl=300)
def fetch_assessment_history(student_id: str, limit: int = 10) -> dict[str, Any]:
    """Fetch assessment history for a student"""
    try:
        return AuthManager.api_get(
            f"/v1/assessments/{student_id}/history",
            params={"limit": limit, "offset": 0},
        )
    except Exception as e:
        st.error(f"Failed to fetch assessment history: {str(e)}")
        return {}


@st.cache_data(ttl=300)
def fetch_evidence(assessment_id: str) -> dict[str, Any]:
    """Fetch evidence for an assessment"""
    try:
        return AuthManager.api_get(f"/v1/evidence/{assessment_id}")
    except Exception as e:
        st.error(f"Failed to fetch evidence: {str(e)}")
        return {}


def show_latest_assessment(assessment: dict[str, Any]) -> None:
    """Display latest assessment details"""

    st.subheader("📊 Latest Assessment")

    # Assessment metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Assessment Date",
            value=assessment.get("assessed_on", "N/A"),
        )

    with col2:
        st.metric(
            label="Class ID",
            value=assessment.get("class_id", "N/A"),
        )

    with col3:
        st.metric(
            label="Model Version",
            value=assessment.get("model_version", "N/A"),
        )

    # Skill scores
    skills = assessment.get("skills", [])
    if not skills:
        st.info("No skill scores available")
        return

    # Prepare skill data for chart
    skill_data = {skill["skill"]: skill["score"] for skill in skills}

    # Display skill chart
    col1, col2 = st.columns([2, 1])

    with col1:
        fig = create_skill_chart(skill_data, title="Current Skill Scores")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Skill Scores:**")
        for skill in skills:
            st.metric(
                label=format_skill_name(skill["skill"]),
                value=f"{skill['score']:.1f}/100",
                delta=None,
                help=f"Confidence: {skill['confidence']:.2f}",
            )


def show_evidence_section(evidence: dict[str, Any]) -> None:
    """Display evidence spans for the assessment"""

    st.subheader("🔍 Supporting Evidence")

    evidence_spans = evidence.get("evidence_spans", [])

    if not evidence_spans:
        st.info("No evidence data available")
        return

    # Group evidence by skill
    evidence_by_skill = {}
    for span in evidence_spans:
        skill = span.get("skill", "unknown")
        if skill not in evidence_by_skill:
            evidence_by_skill[skill] = []
        evidence_by_skill[skill].append(span)

    # Display evidence by skill in expandable sections
    for skill, spans in evidence_by_skill.items():
        with st.expander(f"**{format_skill_name(skill)}** ({len(spans)} evidence spans)"):
            for i, span in enumerate(spans, 1):
                st.markdown(f"**Evidence {i}:**")
                st.markdown(f"_{span.get('span_text', 'N/A')}_")
                st.caption(f"📍 Location: {span.get('span_location', 'N/A')}")
                if span.get("rationale"):
                    st.info(f"💡 {span['rationale']}")
                if span.get("score_contribution"):
                    st.caption(f"Contribution: {span['score_contribution']:.2f}")
                st.divider()


def show_assessment_history(history: dict[str, Any], student_id: str) -> None:
    """Display assessment history and trends"""

    st.subheader("📈 Assessment History & Trends")

    assessments = history.get("assessments", [])
    total = history.get("total", 0)

    st.write(f"Showing {len(assessments)} of {total} total assessments")

    # Prepare data for trends
    trend_data = []
    for assessment in assessments:
        row = {"assessed_on": assessment["assessed_on"]}
        for skill in assessment.get("skills", []):
            row[skill["skill"]] = skill["score"]
        trend_data.append(row)

    if not trend_data:
        st.info("Not enough data for trends")
        return

    df = pd.DataFrame(trend_data)
    df["assessed_on"] = pd.to_datetime(df["assessed_on"])

    # Display trend charts for each skill
    skills = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]

    # Create tabs for each skill
    tabs = st.tabs([format_skill_name(skill) for skill in skills])

    for tab, skill in zip(tabs, skills):
        with tab:
            if skill in df.columns:
                fig = create_trend_chart(
                    df, skill, title=f"{format_skill_name(skill)} Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No data available for {format_skill_name(skill)}")

    # Assessment history table
    st.markdown("### 📋 Assessment History Table")

    table_data = []
    for assessment in assessments:
        row = {
            "Assessment ID": str(assessment["assessment_id"]),
            "Date": assessment["assessed_on"],
            "Class ID": assessment.get("class_id", "N/A"),
        }

        # Add skill scores
        for skill in assessment.get("skills", []):
            row[format_skill_name(skill["skill"])] = f"{skill['score']:.1f}"

        table_data.append(row)

    df_table = pd.DataFrame(table_data)

    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    # Export options
    st.markdown("### 📥 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        csv_data = export_to_csv(table_data)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"student_{student_id}_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        pdf_data = export_to_pdf(
            title=f"Student Assessment History",
            data=table_data,
            student_name=f"Student ID: {student_id}",
        )
        st.download_button(
            label="📑 Download as PDF",
            data=pdf_data,
            file_name=f"student_{student_id}_history.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
