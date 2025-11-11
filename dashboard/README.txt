AssessMax Educator Dashboard
============================

A Streamlit-based dashboard for educators to view student assessments and skill progression.

Features
--------
- Class Overview: View class-level metrics and student summaries
- Student Detail: View individual student assessment history
- Trends: Analyze skill progression over time (Coming Soon)
- Uploads & Jobs: Upload transcripts/artifacts and monitor processing

Setup
-----
1. Install dependencies:
   pip install -e .

2. Copy .env.example to .env and configure:
   cp .env.example .env

3. Update .env with your API endpoint and Cognito settings

4. Run the dashboard:
   streamlit run app.py

Accessibility
-------------
- WCAG AA compliant
- Keyboard navigation support
- High contrast colors (4.5:1 minimum)
- Screen reader compatible
- Skip to main content link
- Focus indicators

Export Features
---------------
- Export class data to CSV
- Export class data to PDF
- Export student history to CSV
- Export student history to PDF

Demo Mode
---------
The dashboard includes a demo/development mode with mock authentication.
For production, configure AWS Cognito in the .env file.

API Endpoints Used
------------------
- GET /v1/classes/{class_id}/dashboard - Class overview data
- GET /v1/assessments/{student_id} - Latest student assessment
- GET /v1/assessments/{student_id}/history - Student assessment history
- GET /v1/evidence/{assessment_id} - Assessment evidence spans
- GET /auth/me - Current user information
