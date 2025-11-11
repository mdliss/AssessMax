# Middle School Non-Academic Skills Measurement Engine

**Organization:** Flourish Schools
**Project ID:** JnGyV0Xlx2AEiL31nu7J_1761530509243

---

# Product Requirements Document (PRD)

## 1. Executive Summary

The Middle School Non-Academic Skills Measurement Engine is an AI-driven solution designed to address the challenge of assessing non-academic skills in middle school students, such as empathy and adaptability. This innovative tool provides educators with a scalable, objective, and continuous method to measure and track these skills, thereby facilitating timely interventions and demonstrating growth over time. By analyzing classroom conversation transcripts and project-based work, this system aims to enhance educational outcomes and provide actionable feedback to both educators and students.

## 2. Problem Statement

Middle school educators currently lack scalable tools to effectively measure and track students' non-academic skills, which are critical for real-world success. Traditional methods depend heavily on subjective teacher observations and sporadic evaluations, leading to inefficient interventions and inadequate tracking of skill development. This system fills the gap by continuously analyzing student conversation transcripts and project work to provide objective assessments.

## 3. Goals & Success Metrics

- **Goal**: Provide continuous, automated assessment of non-academic skills.
  - **Success Metric**: Initial ratings are acceptable to teachers.
  - **Success Metric**: Detection of statistically significant skill improvement over 4-12 week periods.

## 4. Target Users & Personas

- **Middle School Educators**: Need objective and scalable tools to assess and support non-academic skill development in students.
- **School Administrators**: Require data-driven insights to track skill development trends and demonstrate educational outcomes.
- **Middle School Students**: Benefit from actionable feedback on their non-academic skills.

## 5. User Stories

1. As a **middle school educator**, I want to receive objective assessments of my students’ non-academic skills so that I can provide timely and targeted support.
2. As a **school administrator**, I want to track skill development trends across cohorts so that I can demonstrate educational outcomes to stakeholders.
3. As a **student**, I want actionable feedback on my non-academic skills so that I can improve and prepare for real-world success.

## 6. Functional Requirements

### P0: Must-have (Critical)
- The system must quantitatively infer a student’s non-academic skill levels from classroom conversation transcripts and project deliverables.
- The system must provide justifying evidence and reasoning for each inference.
- The system must support cloud deployment for scalability and accessibility.
- The system must handle high-performance parallel processing of full days of classroom conversation transcripts and project deliverables.

### P1: Should-have (Important)
- The system should offer a dashboard interface for educators to view and track student skill assessments.
- The system should integrate with existing school management systems for seamless data exchange.

### P2: Nice-to-have (Optional)
- The system could provide predictive analytics to forecast future skill development trajectories.
- The system could offer customizable reporting tools for various stakeholders.

## 7. Non-Functional Requirements

- **Performance**: The system should handle large volumes of data efficiently.
- **Security**: The system must ensure data privacy and compliance with educational data protection regulations.
- **Scalability**: The system should support scaling to accommodate multiple schools and districts.
- **Compliance**: Compliance with relevant educational standards and regulations is required.

## 8. User Experience & Design Considerations

- The interface should be intuitive and accessible for users with varying levels of technical proficiency.
- Key workflows should focus on ease of access to assessments and insights.
- The design should consider accessibility standards to ensure inclusivity.

## 9. Technical Requirements

- **Languages**: Python
- **AI Frameworks**: To be determined based on best fit for NLP and data processing.
- **Cloud Platforms**: AWS preferred but not mandatory.
- **Data Requirements**: Ingest classroom conversation transcripts and project deliverables in supported formats.
- **APIs**: Use publicly available NLP and data processing APIs.
- **Mock Data Sources**: Utilize anonymized and synthetic data for development and testing.

## 10. Dependencies & Assumptions

- The success of the system assumes availability of high-quality conversation transcripts and project deliverables from schools.
- It is assumed that educators will be willing to adopt new technology for assessing non-academic skills.

## 11. Out of Scope

- This version does not include integration with non-educational platforms or systems.
- Advanced predictive analytics and customizable reporting tools are not included in this initial release.

This PRD is designed to align cross-functional stakeholders and enable independent implementation. It focuses on the "what" and "why" of the product, providing a clear roadmap for development without time-based commitments.