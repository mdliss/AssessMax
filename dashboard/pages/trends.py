"""Trends page - Display class and student trends over time"""

import streamlit as st


def show_trends() -> None:
    """Display trends analysis page"""

    st.title("📈 Trends Analysis")
    st.markdown("View skill progression trends over time (4-12 weeks)")

    # Time range selection
    col1, col2 = st.columns([2, 1])

    with col1:
        time_range = st.selectbox(
            "Select Time Range",
            ["4 weeks", "8 weeks", "12 weeks"],
            help="Choose the time period for trend analysis",
        )

    with col2:
        view_type = st.radio("View Type", ["Class", "Student"], horizontal=True)

    st.divider()

    # Class or Student selection
    if view_type == "Class":
        class_id = st.text_input(
            "Enter Class ID",
            value="MATH-7A",
            help="Enter the class identifier",
        )

        if class_id:
            show_class_trends(class_id, time_range)
        else:
            st.info("ℹ️ Please enter a class ID")

    else:  # Student view
        student_id = st.text_input(
            "Enter Student ID (UUID)",
            help="Enter the student's UUID",
        )

        if student_id:
            show_student_trends(student_id, time_range)
        else:
            st.info("ℹ️ Please enter a student ID")


def show_class_trends(class_id: str, time_range: str) -> None:
    """Display class-level trends"""

    st.subheader(f"📊 Class Trends - {class_id}")

    st.info(
        """
        **Coming Soon**

        This feature will display:
        - Class average skill scores over time
        - Skill progression trends
        - Student participation rates
        - Assessment frequency
        """
    )

    # Placeholder for trend visualization
    st.markdown("### 📈 Skill Progression")
    st.write(f"Time range: {time_range}")


def show_student_trends(student_id: str, time_range: str) -> None:
    """Display student-level trends"""

    st.subheader(f"👤 Student Trends - {student_id}")

    st.info(
        """
        **Coming Soon**

        This feature will display:
        - Individual skill score progression
        - Comparison with class averages
        - Growth rate analysis
        - Skill strengths and areas for improvement
        """
    )

    # Placeholder for trend visualization
    st.markdown("### 📈 Personal Growth")
    st.write(f"Time range: {time_range}")
