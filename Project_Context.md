Here is the complete Project Context document (Project_Context.md) for TrialAgent NLP, incorporating both your frontend privacy guardrail and the Gemini 3.5 Flash-Lite model specification so you can copy it directly into your file or share it with Claude:
Core Concept & Product Vision
TrialAgent NLP is an open-access, zero-PII, stateless clinical trial matching platform built to remove friction between patients/caregivers and live clinical research registries.
Instead of forcing users to navigate dense government databases filled with complex medical terminology—or forcing them to create accounts and upload sensitive medical records to third-party servers—TrialAgent NLP acts as an ephemeral translation and matching layer. Users paste raw, unstructured diagnostic notes (such as a biopsy summary or pathology line), and the system instantly extracts clinical criteria, queries live trials on ClinicalTrials.gov, evaluates eligibility criteria, and outputs a structured set of matching protocols paired with a personalized Doctor Discussion Guide.
Privacy-First & Zero-PII Architecture (Healthcare Compliance Design)
To ensure strict adherence to healthcare data privacy standards and avoid storing or exposing Protected Health Information (PHI) or Personally Identifiable Information (PII), the system is engineered around defense-in-depth data minimization and zero-persistence:
Frontend UI Privacy Guardrail (Explicit User Warning):
The input interface prominently instructs users not to enter PII/PHI (no names, dates of birth, Medical Record Numbers, addresses, or contact details)—limiting input strictly to clinical diagnosis, staging, biomarkers, and city.
No User Accounts or Authentication:
There is no sign-up, login, email collection, or user profiling. Anyone can access the tool anonymously.
100% Stateless Execution (Zero Database Layer):
The application has no database attached (no PostgreSQL, MongoDB, Redis persistence, or S3 storage).
All processing happens entirely in volatile memory (RAM) during the lifecycle of a single HTTP request. Once the Server-Sent Events (SSE) stream closes and the response renders on the client's screen, all variables are garbage-collected and permanently erased.
Backend Sanitization Fail-Safe (Agent 1):
As a secondary defense-in-depth layer, Agent 1 (powered by Gemini 3.5 Flash-Lite) acts as a strict sanitization filter in volatile memory before any external API call is made.
Even if a user ignores the UI warning and pastes a clinical note containing personal identifiers, Agent 1 is explicitly prompted to discard all PII/PHI and output a sanitized JSON object containing only four non-identifying clinical attributes:
condition (e.g., Non-Small Cell Lung Cancer)
stage (e.g., Stage IIIa)
biomarkers (e.g., EGFR Exon 19 deletion, PD-L1 45%)
city (e.g., Atlanta)
No Server-Side Payload Logging:
Backend FastAPI middleware is configured to suppress request-body logging so raw user inputs never appear in Vercel runtime logs or console traces.
External API Isolation:
ClinicalTrials.gov only ever receives clean, anonymized search parameters (condition string + city string) from our backend—never the user's raw text or IP-linked identity.
End-to-End Multi-Agent Workflow
[ User Input: Unstructured Clinical Note (UI warns against PII) ]
                    │
                    ▼ (In-Memory Request)
┌───────────────────────────────────────┐
│ AGENT 1: Sanitization & Extraction    │ ──> Model: Gemini 3.5 Flash-Lite
│ - Strips any accidental PII/PHI       │ ──> Outputs clean JSON (Condition, Stage, Biomarkers, City)
└───────────────────┬───────────────────┘
                    │
                    ▼ (Anonymized Query Parameters)
┌───────────────────────────────────────┐
│ AGENT 2: Live Registry Retrieval      │ ──> Endpoint: ClinicalTrials.gov v2 REST API
│ - Filters for RECRUITING status       │ ──> Fetches raw protocol titles, NCT IDs, & eligibility text
└───────────────────┬───────────────────┘
                    │
                    ▼ (Batched Protocol Evaluation)
┌───────────────────────────────────────┐
│ AGENT 3: Eligibility & Guidance       │ ──> Model: Gemini 3.5 Flash-Lite
│ - Cross-references biomarkers/stage   │ ──> Scores compatibility & generates 5-question Doctor Guide
└───────────────────┬───────────────────┘
                    │
                    ▼ (Graceful Fallback Check)
     [ Render Results via SSE Stream ]
Step-by-Step Pipeline Breakdown:
Step 1: Streaming Initiation (Next.js + FastAPI SSE)
When the user submits their note, the Next.js frontend opens a Server-Sent Events (SSE) connection to the Python FastAPI serverless backend, displaying real-time status updates as each agent executes.
Step 2: Agent 1 — Clinical Entity Extraction (Gemini 3.5 Flash-Lite)
Uses low-latency structured JSON output from Gemini 3.5 Flash-Lite to parse messy medical shorthand into clean parameters while stripping any personal identifiers.
Step 3: Agent 2 — Live Registry Query (ClinicalTrials.gov v2 API)
Queries the official ClinicalTrials.gov v2 REST endpoint for actively recruiting trials matching the extracted condition and geographic location, pulling protocol summaries, NCT identifiers, facility locations, and inclusion/exclusion criteria.
Step 4: Agent 3 — Batched Evaluation & Doctor Checklist (Gemini 3.5 Flash-Lite)
Sends the extracted clinical profile alongside the retrieved trial inclusion/exclusion rules to Gemini 3.5 Flash-Lite in a single batched inference call.
Generates trial compatibility insights and synthesizes a plain-language 5-Question Doctor Discussion Guide tailored to the patient's exact biomarkers and stage so they can have an informed conversation with their oncologist.
Step 5: Graceful Fallback Resilience
If API rate limits, network timeouts, or parsing errors interrupt Agent 3's automated compatibility scoring, the pipeline does not crash. Instead, it triggers a Partial Results (Manual Review) state—displaying a clear status banner while still delivering all retrieved NCT trials and the generated Doctor Discussion Guide.
Complete Tech Stack
Frontend: Next.js (React), deployed on Vercel, using Server-Sent Events (SSE) for live pipeline progress streaming.
Backend: Python FastAPI running as serverless functions on Vercel.
AI / LLM Model: Gemini 3.5 Flash-Lite (chosen for ultra-fast inference, structured JSON reliability, and low-latency batched evaluation).
External Data API: ClinicalTrials.gov v2 REST API (live, unauthenticated public government data).
Storage / Database: None (100% stateless in-memory architecture).
Reference Test Scenarios (For Context & Validation)
Scenario 1: Localized Urologic Oncology
Input: Diagnosis: Stage II Prostate Adenocarcinoma; Stage: Stage II; Biomarkers: PSA 8.5 ng/mL, Gleason Score 7 (3+4); City: Seattle.
Focus: Demonstrates extraction of lab values (PSA 8.5 ng/mL) and pathology grading (Gleason Score 7), local Seattle trial lookup, and urology-specific consultation questions.
Scenario 2: Biomarker-Driven Thoracic Oncology
Input: Diagnosis: Stage IIIa Non-Small Cell Lung Cancer; Stage: Stage IIIa; Biomarkers: EGFR Exon 19 deletion (+), ALK (-), PD-L1 (45%); City: Atlanta.
Focus: Demonstrates multi-biomarker parsing (EGFR+, ALK-, PD-L1 45%), complex eligibility cross-referencing, and graceful fallback handling.
