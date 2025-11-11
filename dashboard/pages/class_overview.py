"""Class Overview page - Display class-level metrics and student summaries"""

from typing import Any

import pandas as pd
import streamlit as st

from auth import AuthManager
from utils import create_skill_chart, export_to_csv, export_to_pdf, format_skill_name


def show_class_overview() -> None:
    """Display class overview with metrics and student summaries"""

    st.title("🏫 Class Overview")
    st.markdown("View class-level assessment metrics and student summaries")

    # Class selection
    col1, col2 = st.columns([2, 1])

    with col1:
        class_id = st.text_input(
            "Enter Class ID",
            value="MATH-7A",
            help="Enter the class identifier to view",
            label_visibility="visible",
        )

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not class_id:
        st.info("ℹ️ Please enter a class ID to view data")
        return

    # Fetch class data
    try:
        with st.spinner("Loading class data..."):
            data = fetch_class_dashboard(class_id)

        if not data:
            st.warning(f"⚠️ No data found for class: {class_id}")
            return

        metrics = data.get("metrics", {})
        students = data.get("students", [])

        # Display class metrics
        show_class_metrics(metrics)

        st.divider()

        # Display class average skill scores
        show_class_averages(metrics)

        st.divider()

        # Display student summaries
        show_student_summaries(students, class_id)

    except Exception as e:
        st.error(f"❌ Error loading class data: {str(e)}")
        st.info("💡 Make sure the backend API is running at the configured URL")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_class_dashboard(class_id: str) -> dict[str, Any]:
    """
    Fetch class dashboard data from API

    Args:
        class_id: Class identifier

    Returns:
        Class dashboard data
    """
    try:
        return AuthManager.api_get(f"/v1/classes/{class_id}/dashboard")
    except Exception as e:
        st.error(f"Failed to fetch class data: {str(e)}")
        return {}


def show_class_metrics(metrics: dict[str, Any]) -> None:
    """Display class-level metrics"""

    st.subheader("📊 Class Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        student_count = metrics.get("student_count", 0)
        st.metric(
            label="Total Students",
            value=student_count,
            help="Number of students in the class",
        )

    with col2:
        total_assessments = metrics.get("total_assessments", 0)
        st.metric(
            label="Total Assessments",
            value=total_assessments,
            help="Total number of assessments conducted",
        )

    with col3:
        avg_per_student = (
            total_assessments / student_count if student_count > 0 else 0
        )
        st.metric(
            label="Avg Assessments/Student",
            value=f"{avg_per_student:.1f}",
            help="Average number of assessments per student",
        )

    with col4:
        date_range = metrics.get("date_range")
        if date_range and len(date_range) == 2:
            days = (date_range[1] - date_range[0]).days
            st.metric(
                label="Date Range (days)",
                value=days,
                help="Number of days covered by assessments",
            )
        else:
            st.metric(label="Date Range", value="N/A")


def show_class_averages(metrics: dict[str, Any]) -> None:
    """Display class average skill scores"""

    st.subheader("📈 Class Average Skill Scores")

    class_averages = metrics.get("class_averages", {})

    if not class_averages:
        st.info("No skill score data available")
        return

    # Display as radar chart
    col1, col2 = st.columns([2, 1])

    with col1:
        fig = create_skill_chart(class_averages, title="Class Average Skill Scores")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Skill Breakdown:**")
        for skill, score in class_averages.items():
            st.metric(
                label=format_skill_name(skill),
                value=f"{score:.1f}/100",
                help=f"Class average for {format_skill_name(skill)}",
            )


def show_student_summaries(students: list[dict[str, Any]], class_id: str) -> None:
    """Display student summary table"""

    st.subheader("👥 Student Summaries")

    if not students:
        st.info("No student data available")
        return

    # Prepare data for display
    table_data = []
    for student in students:
        latest = student.get("latest_assessment")
        avg_scores = student.get("average_scores", {})

        # Calculate overall average
        overall_avg = (
            sum(avg_scores.values()) / len(avg_scores)
            if avg_scores
            else 0
        )

        row = {
            "Student ID": str(student["student_id"]),
            "Name": student["name"],
            "Assessment Count": student["assessment_count"],
            "Last Assessed": (
                latest["assessed_on"] if latest else "N/A"
            ),
            "Overall Average": f"{overall_avg:.1f}",
        }

        # Add individual skill averages
        for skill in ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]:
            if skill in avg_scores:
                row[format_skill_name(skill)] = f"{avg_scores[skill]:.1f}"
            else:
                row[format_skill_name(skill)] = "N/A"

        table_data.append(row)

    df = pd.DataFrame(table_data)

    # Display table with sorting
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    # Export options
    st.markdown("### 📥 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        # CSV export
        csv_data = export_to_csv(table_data)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"class_{class_id}_overview.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        # PDF export
        pdf_data = export_to_pdf(
            title=f"Class Overview - {class_id}",
            data=table_data,
            class_id=class_id,
        )
        st.download_button(
            label="📑 Download as PDF",
            data=pdf_data,
            file_name=f"class_{class_id}_overview.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
