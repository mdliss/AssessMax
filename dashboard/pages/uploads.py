"""Uploads and Jobs page - Manage file uploads and view job status"""

import streamlit as st


def show_uploads() -> None:
    """Display uploads and jobs management page"""

    st.title("📁 Uploads & Jobs")
    st.markdown("Upload transcripts/artifacts and monitor processing jobs")

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📤 Upload Files", "⚙️ Job Status", "📊 Upload History"])

    with tab1:
        show_upload_section()

    with tab2:
        show_job_status_section()

    with tab3:
        show_upload_history_section()


def show_upload_section() -> None:
    """Display file upload interface"""

    st.subheader("📤 Upload Transcripts or Artifacts")

    # Upload type selection
    upload_type = st.radio(
        "Upload Type",
        ["Transcript", "Artifact"],
        help="Select whether you're uploading a transcript or artifact",
        horizontal=True,
    )

    if upload_type == "Transcript":
        show_transcript_upload()
    else:
        show_artifact_upload()


def show_transcript_upload() -> None:
    """Display transcript upload form"""

    st.markdown("### 📝 Upload Classroom Transcript")

    with st.form("transcript_upload_form"):
        # File upload
        uploaded_file = st.file_uploader(
            "Choose transcript file",
            type=["jsonl", "csv", "txt"],
            help="Upload transcript in JSONL, CSV, or TXT format",
        )

        # Metadata
        col1, col2 = st.columns(2)

        with col1:
            class_id = st.text_input(
                "Class ID",
                help="Enter the class identifier",
                label_visibility="visible",
            )

        with col2:
            transcript_date = st.date_input(
                "Transcript Date",
                help="Date of the classroom session",
                label_visibility="visible",
            )

        student_roster = st.text_area(
            "Student Roster",
            help="Enter student IDs, one per line",
            placeholder="student-uuid-1\nstudent-uuid-2\n...",
        )

        source = st.text_input(
            "Source",
            help="Source of the transcript (e.g., Zoom, Google Meet)",
            placeholder="e.g., Zoom Recording",
        )

        submit = st.form_submit_button("📤 Upload Transcript", use_container_width=True)

        if submit:
            if not uploaded_file:
                st.error("❌ Please select a file to upload")
            elif not class_id:
                st.error("❌ Please enter a class ID")
            else:
                st.success("✅ Transcript upload initiated!")
                st.info(
                    "**Note:** This is a demo interface. "
                    "In production, this would upload the file to the API."
                )


def show_artifact_upload() -> None:
    """Display artifact upload form"""

    st.markdown("### 📎 Upload Student Artifact")

    with st.form("artifact_upload_form"):
        # File upload
        uploaded_file = st.file_uploader(
            "Choose artifact file",
            type=["pdf", "docx", "png", "jpg", "jpeg"],
            help="Upload artifact in PDF, DOCX, PNG, or JPG format",
        )

        # Metadata
        col1, col2 = st.columns(2)

        with col1:
            student_id = st.text_input(
                "Student ID (UUID)",
                help="Enter the student UUID",
                label_visibility="visible",
            )

        with col2:
            artifact_date = st.date_input(
                "Artifact Date",
                help="Date the artifact was created",
                label_visibility="visible",
            )

        artifact_type = st.selectbox(
            "Artifact Type",
            ["Essay", "Project", "Presentation", "Other"],
            help="Select the type of artifact",
        )

        description = st.text_area(
            "Description",
            help="Optional description of the artifact",
            placeholder="Enter a brief description...",
        )

        submit = st.form_submit_button("📤 Upload Artifact", use_container_width=True)

        if submit:
            if not uploaded_file:
                st.error("❌ Please select a file to upload")
            elif not student_id:
                st.error("❌ Please enter a student ID")
            else:
                st.success("✅ Artifact upload initiated!")
                st.info(
                    "**Note:** This is a demo interface. "
                    "In production, this would upload the file to the API."
                )


def show_job_status_section() -> None:
    """Display job status monitoring"""

    st.subheader("⚙️ Processing Job Status")

    # Job ID input
    job_id = st.text_input(
        "Enter Job ID",
        help="Enter the job ID to check status",
        placeholder="job-uuid",
    )

    if job_id:
        st.info(
            """
            **Coming Soon**

            This feature will display:
            - Current job status (pending, running, completed, failed)
            - Processing progress
            - Error messages if any
            - Job logs and details
            """
        )

        # Placeholder status
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Job Status", "Running")

        with col2:
            st.metric("Progress", "75%")

        with col3:
            st.metric("Time Elapsed", "2m 30s")
    else:
        st.info("ℹ️ Enter a job ID to view status")


def show_upload_history_section() -> None:
    """Display upload history"""

    st.subheader("📊 Upload History")

    st.info(
        """
        **Coming Soon**

        This feature will display:
        - Recent uploads
        - Upload status and results
        - Processing times
        - Error reports
        - File metadata
        """
    )

    # Placeholder table
    st.markdown("### Recent Uploads")
    st.write("No upload history available in demo mode")
