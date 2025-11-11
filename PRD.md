# Middle School Non-Academic Skills Measurement Engine — MVP Product Requirements Document

Project: Middle School Non-Academic Skills Measurement Engine — AI assessments from classroom transcripts and project artifacts
Goal: Deliver a compliant, explainable, school-deployable MVP that ingests transcripts and artifacts, infers non-academic skills (e.g., empathy, adaptability, collaboration), explains the evidence for each inference, and tracks changes over time for cohorts and individuals.
Note: Post-MVP items like advanced forecasting, district-wide integrations, and customizable reporting templates are excluded from the MVP and deferred to Phase 2+.

## Core Architecture (MVP)

Primary Architecture Decision: Python-first, API-centric backend (FastAPI) with an AWS reference architecture and a modular NLP pipeline built on Hugging Face + spaCy + NLTK; Streamlit dashboard for educator UX; Auth via AWS Cognito; data persisted in AWS RDS (PostgreSQL) for normalized assessments and DynamoDB for pipeline metadata and batch status.

- MVP features a single, multi-tenant FastAPI service exposing ingestion, processing, scoring, evidence extraction, and reporting endpoints.
- Not included in MVP: cross-district SSO federation, LTI 1.3 integration, custom rubric designers, fine-tuned large models, and predictive trajectories.
- Single shared compute resource approach: one autoscaling group per environment; asynchronous jobs offloaded to AWS Lambda with SQS; long-running batch orchestrated via Step Functions.
- Future: add model-specific microservices, vector database retrieval, LTI integration, and multi-region active-active replication.

URL Structure:
- /healthz — health check
- /auth/* — Cognito hosted UI and callback routes
- /v1/ingest/transcripts — POST classroom transcripts (JSON, CSV, TXT) with metadata
- /v1/ingest/artifacts — POST student artifacts (PDF, DOCX, images) to S3 presigned URLs
- /v1/pipeline/run — POST trigger batch scoring for a class/day
- /v1/assessments/{student_id} — GET latest skill scores + evidence
- /v1/assessments/{student_id}/history — GET time-series
- /v1/classes/{class_id}/dashboard — GET class rollup
- /v1/evidence/{assessment_id} — GET evidence spans, rationales, and citations
- /v1/admin/jobs/{job_id} — GET job status and logs

## User Stories

Primary User: Middle School Educator (MVP Priority)
- As an educator, I want to upload or point to the prior day’s transcripts so that the system can score today’s skills.
- As an educator, I want clear skill scores with plain-language evidence so I can discuss it with students.
- As an educator, I want a class dashboard so I can spot who needs support and who is improving.
- As an educator, I want to export a weekly snapshot so I can share progress in team meetings.
- As an educator, I want confidence thresholds and error flags so I do not over-trust weak signals.

Note: Complete all educator stories before admin and student views.

Secondary User: School Administrator (Implement after Educator)
- As an administrator, I want cohort trendlines so I can report growth over a 4–12 week window.
- As an administrator, I want audit logs and permissions so I know who accessed which student data.

## Key Features for MVP

1) Authentication System
Must Have:
- Email/password login via Cognito; optional SAML/OIDC is future work.
- Secure sessions stored as HTTP-only cookies.
- Role-based access: educator, admin, read_only.
- Display name logic: default to verified email localpart; admins can set canonical display names; truncate to 40 chars with ellipsis.
Success Criteria:
- User can create accounts and maintain sessions across refreshes.
- Unique user IDs and stable display names.

2) Ingestion and Normalization
Must Have:
- Accept transcripts: JSONL, CSV, TXT. Accept artifacts: PDF/DOCX/PNG/JPG. Size <= 50MB/file in MVP.
- Require metadata: class_id, student_roster, date, source.
- Normalize to canonical schema: utterances with timestamps, speaker roles, student linkage, artifact references.
- Performance: sustain 8 classroom-days/hour per t3.large baseline; batchable.
Success Criteria:
- 100% of accepted formats stored in S3 with metadata in DynamoDB.
- Canonicalized records available to pipeline within <2 minutes of upload.

3) NLP Scoring and Evidence Extraction
Must Have:
- Rule-of-thumb skills: empathy, adaptability, collaboration, communication clarity, self-regulation.
- Pipeline stages: language detection -> cleanup -> sentence segmentation -> diarization mapping -> skill cue detection -> scoring -> explanation extraction.
- Methods: tokenization (spaCy), classic features (NLTK), transformer encoders (Hugging Face) for classification; calibration with Platt scaling or temperature scaling.
- Evidence: for each score, return ranked text spans with rationales; cite transcript line numbers or artifact pages.
- Constraints: deterministic seeds for reproducibility; configurable thresholds.
Success Criteria:
- First teacher review finds outputs reasonable on >=70% of samples.
- Evidence spans map to exact lines/pages with offsets.

4) Dashboard GUI
Must Have:
- Streamlit dashboard MVP; alternative Dash or lightweight React acceptable.
- Views: Class Overview, Student Detail, Trends 4–12 weeks, Uploads and Jobs, Data Quality Flags.
- Accessibility: WCAG AA color contrast; font size controls.
- Export CSV/PDF summary.
Success Criteria:
- Educators can locate a student’s latest assessment in <10 seconds.
- Weekly export generated in <5 seconds for a class of 30.

5) State Persistence and History
Must Have:
- PostgreSQL schema for assessments, evidence, and aggregates.
- DynamoDB tables for job runs and pipeline artifacts.
- S3 versioning for raw inputs and anonymized dev copies.
Success Criteria:
- Reprocess any job from raw inputs using job metadata.
- Full audit trail for assessments and evidence.

6) Deployment
Must Have:
- AWS reference stack: EC2 or Fargate for FastAPI, S3 for storage, Lambda for async tasks, SQS, Step Functions, RDS Postgres, DynamoDB, CloudWatch, Cognito.
- Docker images built in CI; GitHub Actions pipeline with tests, security scans, and deploy gates.
- Environment separation: dev, staging, prod.
Success Criteria:
- Public URL reachable; supports 50 concurrent educator sessions.
- No downtime during routine deploys; blue/green or rolling updates.

## Data Model

PostgreSQL (RDS) — Core Assessments
Tables:
- students(student_id PK, class_id, name, external_ref, created_at)
- assessments(assessment_id PK, student_id FK, class_id, assessed_on, model_version, empathy, adaptability, collaboration, communication, self_regulation, confidence_empathy, ..., created_at)
- evidence(evidence_id PK, assessment_id FK, skill, span_text, span_location, rationale, score_contrib, created_at)
- class_aggregates(class_id, window_start, window_end, metric_name, metric_value, created_at)

DynamoDB — Pipeline Metadata
- jobs PK: job_id with status, class_id, date, input_keys, output_keys, error, started_at, ended_at.
- artifacts PK: artifact_key with uploader_id, class_id, content_type, sha256, created_at.

S3 Layout
- raw/{env}/{class_id}/{date}/transcripts/*.jsonl|csv|txt
- raw/{env}/{class_id}/{date}/artifacts/*.pdf|docx|png
- normalized/{env}/{job_id}/transcript.jsonl
- outputs/{env}/{job_id}/scores.json

Why Two Databases?
RDS for relational queries and history; DynamoDB for high-volume metadata and fast job lookups.

## Recommended Tech Stack (MVP)

Language: Python
AI/NLP: Hugging Face Transformers, spaCy, NLTK
API Backend: FastAPI with UVicorn/Gunicorn
Cloud: AWS (EC2/Fargate, S3, Lambda, Step Functions, SQS, Cognito)
Dashboard GUI: Streamlit (primary) / Dash / React (future)
Database: AWS RDS (PostgreSQL) + DynamoDB
Auth: Cognito (Auth0 optional later)
DevOps: Docker, GitHub Actions, CloudWatch, Parameter Store/Secrets Manager

Pitfalls to Watch:
- Transcript diarization mismatches; enforce roster mapping and role tags.
- Explainability drift; maintain calibration sets and regression tests.
- FERPA/PPRA compliance; strictly segregate environments and logs.

## Out of Scope for MVP
- LTI 1.3/Google Classroom/PowerSchool integrations.
- Forecasting future trajectories.
- Custom rubric builders.
- Multi-district reporting with SSO federation.
- Fine-tuned LLMs hosted on custom GPU clusters.

## Known Limitations and Trade-offs
1) Diarization is taken as given by transcripts; no speech-to-text in MVP.
2) Scores rely on English pipeline; multilingual is future work.
3) Model versions are fixed per environment; hot-swap requires reprocessing.
4) Streamlit UX is single-page; advanced UX deferred.
5) Batch windows daily; sub-hour near-real-time is future work.

## Success Metrics for MVP Checkpoint
1) Teachers mark >=70% of outputs as reasonable on blind review.
2) Reprocessing a day’s class completes in <30 minutes with t3.large equivalent.
3) Evidence spans resolve to exact transcript lines/pages >=95% of the time.
4) Weekly cohort trendlines compute in <5 seconds for a class of 30.
5) No P1 security issues; audit logs complete and immutable.

## MVP Testing Checklist
Core Functionality
- [ ] Upload transcripts and artifacts; normalized view appears.
- [ ] Trigger job; job status moves queued -> running -> succeeded.
- [ ] Assessments visible in dashboard and via API.
- [ ] Evidence spans clickable to source lines/pages.
Educator Flows
- [ ] Class Overview loads under 2s.
- [ ] Student Detail shows last three assessments.
- [ ] Weekly Export produces CSV and PDF.
Resilience
- [ ] Retry on Lambda timeouts.
- [ ] Step Functions handles partial failures.
- [ ] Idempotent job restarts by job_id.
Security
- [ ] Only class educators and admins can view class data.
- [ ] All access logged to CloudWatch and RDS audit tables.

## Risk Mitigation
Biggest Risk: Low label quality in transcripts.
Mitigation: Strict schema validation, missing-speaker heuristics, teacher feedback loop.
Second Risk: Model overconfidence.
Mitigation: Calibrated probabilities, threshold gating, confidence badges in UI.
Third Risk: PII leakage.
Mitigation: S3 bucket policies, KMS encryption, tokenized IDs, redaction pipeline for dev copies.
Fourth Risk: Cost overruns.
Mitigation: Batch windows, autoscaling policies, metrics-based rightsizing, per-class quotas.

## Technology Choices Rationale
- Python: ecosystem for NLP and scientific tooling.
- Hugging Face + spaCy + NLTK: transformer accuracy, robust NLP primitives, classic features.
- FastAPI: async performance, type hints, OpenAPI auto-docs.
- AWS: compliance primitives, managed auth, mature observability.
- PostgreSQL + DynamoDB: relational analytics + fast metadata.
- Streamlit: fastest educator-usable UX for MVP.

## References
- Project PRD: PRD.txt
- Task List: TASKS.txt
- Architecture: ARCHITECTURE.txt