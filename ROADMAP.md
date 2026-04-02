# PokerFX Web — Roadmap

> Video-based poker hand detection and review tool

## Overview

PokerFX Web is a full-stack web application that processes poker hand videos through a computer-vision pipeline (card detection via PokerFX), then lets you review and export verified hand histories.

**Stack:** React + Tailwind (frontend) · FastAPI (backend) · AWS Batch (card detection) · SQLite (local DB)

---

## Milestones

### v0.1 — Backend Core
*Target: minimal end-to-end upload pipeline*

- [x] #2 Phase 1: FastAPI scaffold + video upload endpoint
- [x] #3 Phase 1: Video status + detected hands CRUD + SQLite schema
- [x] #4 Phase 1: Backend smoke test — upload, poll, DB write

---

### v0.2 — Processing Pipeline
*Target: AWS Batch worker that extracts frames and runs card detection*

- [x] #5 Phase 2: AWS Batch infrastructure (job definition, compute env, queue, IAM)
- [x] #6 Phase 2: Worker — video frame extraction → PokerFX card detection → write results
- [x] #7 Phase 2: Backend job queue integration (submit + poll)

---

### v0.3 — Frontend Integration
*Target: connect React UI to real backend API*

- [x] #8 Phase 3: Connect UploadPage to real API (upload progress, error handling, redirect)
- [x] #9 Phase 3: Connect ReviewPage to real API (polling, hand grid from DB)

---

### v0.4 — Review & Export
*Target: accept/reject detected hands and export verified histories*

- [x] #10 Phase 4: Accept/reject hands (individual + bulk) with confidence indicators
- [x] #11 Phase 4: Export verified hand history (CSV + JSON)

---

### v0.5 — Polish & Launch
*Target: production hardening and documentation*

- [x] #12 Phase 5: Error handling, loading states, empty states, retry logic
- [x] #13 Phase 5: README, API docs, deployment docs

---

## Future

> Not yet scheduled — backburner / research

- [x] #14 Future: User custom card graphics & asset packs (Remotion)
- [x] #15 ASR Research: Voice-to-Board Transcription for Vlog Workflow
- [x] #16 Research: OpenRouter + AWS Bedrock as Multi-Provider Inference Layer
- [x] #17 Feature: Fuse ASR Transcript with Card Detection for Auto-Populated Board/Opponent Cards
- [x] #18 Worker: Audio Extraction + ASR Inference Pipeline

---

## Project

GitHub Project: https://github.com/orgs/phillyc/projects/pokerfx-web/

**Columns:** Backlog → In Progress → Done

| # | Title | Milestone |
|---|-------|-----------|
| #2 | Phase 1: FastAPI scaffold + video upload | v0.1 |
| #3 | Phase 1: Video status + detected hands CRUD | v0.1 |
| #4 | Phase 1: Backend smoke test | v0.1 |
| #5 | Phase 2: AWS Batch infrastructure | v0.2 |
| #6 | Phase 2: Worker — frame extraction + card detection | v0.2 |
| #7 | Phase 2: Backend job queue integration | v0.2 |
| #8 | Phase 3: Connect UploadPage to real API | v0.3 |
| #9 | Phase 3: Connect ReviewPage to real API | v0.3 |
| #10 | Phase 4: Accept/reject hands | v0.4 |
| #11 | Phase 4: Export hand history (CSV + JSON) | v0.4 |
| #12 | Phase 5: Error handling, loading states, retry | v0.5 |
| #13 | Phase 5: README, API docs, deployment docs | v0.5 |
| #14 | Future: Custom card graphics & asset packs | Future |
| #15 | ASR Research: Voice-to-Board Transcription | Future |
| #16 | Research: OpenRouter + AWS Bedrock inference | Future |
| #17 | Feature: Fuse ASR + Card Detection | Future |
| #18 | Worker: Audio Extraction + ASR Pipeline | Future |

---

*Last updated: 2026-04-02*
