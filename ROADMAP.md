# PokerFX Web — Roadmap

> Video-based poker hand detection and review tool.
> Frontend: React + Vite + Tailwind. Backend: FastAPI. ML: AWS Batch + PokerFX card detection model.

## Overview

```
User uploads poker video
        ↓
Backend queues video for AWS Batch processing
        ↓
PokerFX card detection runs → detects individual hands
        ↓
User reviews detected hands (accept/reject)
        ↓
Export verified hand history (CSV/JSON)
```

---

## Phases

### Phase 0 — Repo Foundation
*Setup the project for tracked, collaborative development.*

- [ ] **[#1](https://github.com/phillyc/pokerfx-web/issues/1)** — Set up GitHub Project board + milestone structure + repo description

---

### Phase 1 — Backend API Core
*FastAPI backend with video upload, job queue, and data persistence.*

- [ ] **[#2](https://github.com/phillyc/pokerfx-web/issues/2)** — FastAPI scaffold + video upload endpoint (multipart, local file storage)
- [ ] **[#3](https://github.com/phillyc/pokerfx-web/issues/3)** — FastAPI: video status + detected hands CRUD + SQLite schema
- [ ] **[#4](https://github.com/phillyc/pokerfx-web/issues/4)** — Backend smoke test: upload a video, poll status, verify DB write

---

### Phase 2 — Video Processing Pipeline
*AWS Batch infrastructure and the worker that runs PokerFX card detection.*

- [ ] **[#5](https://github.com/phillyc/pokerfx-web/issues/5)** — AWS Batch infrastructure (job definition, compute environment, queue, IAM roles)
- [ ] **[#6](https://github.com/phillyc/pokerfx-web/issues/6)** — Worker: video frame extraction → PokerFX card detection → write detected hands to DB
- [ ] **[#7](https://github.com/phillyc/pokerfx-web/issues/7)** — End-to-end pipeline test: upload video → job queued → hands written → status updated

---

### Phase 3 — Frontend ↔ Backend Integration
*Wire the React UI to real API endpoints.*

- [ ] **[#8](https://github.com/phillyc/pokerfx-web/issues/8)** — Connect UploadPage to real API (upload progress, error handling, redirect to review)
- [ ] **[#9](https://github.com/phillyc/pokerfx-web/issues/9)** — Connect ReviewPage to real API (status polling, hand grid from DB)

---

### Phase 4 — Review & Verification UX
*The core user interaction: accepting/rejecting detected hands and exporting results.*

- [ ] **[#10](https://github.com/phillyc/pokerfx-web/issues/10)** — Accept/reject hands (individual + bulk), confidence indicators
- [ ] **[#11](https://github.com/phillyc/pokerfx-web/issues/11)** — Export verified hand history (CSV + JSON)

---

### Phase 5 — Polish & Production
*Robustness, documentation, and production readiness.*

- [ ] **[#12](https://github.com/phillyc/pokerfx-web/issues/12)** — Error handling, loading states, empty states, retry logic
- [ ] **[#13](https://github.com/phillyc/pokerfx-web/issues/13)** — README, API docs, deployment docs

---

## Issue Conventions

- Each issue = one reviewable, mergeable unit of work
- Branch naming: `issue/N` (e.g. `issue/5`)
- PR must pass CI (build + type check) before merge
- Each issue closed = demo-able milestone

## Tech Stack Reference

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind 4, TypeScript, React Router 7 |
| Backend | FastAPI (Python), Uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| File Storage | Local filesystem (dev) / S3 (prod) |
| ML Compute | AWS Batch + PokerFX card detection model |
| Hosting | GitHub Pages (frontend), Railway/Render (backend TBD) |
| CI/CD | GitHub Actions |

## API Contract (v1)

```
POST   /api/videos              → upload video, returns {videoId, status}
GET    /api/videos/:id          → {id, filename, status, clipCount, detectedCount, verifiedCount}
GET    /api/videos/:id/hands    → [{id, clipNumber, cards, confidence, status}]
PATCH  /api/videos/:id/hands/:handId → {status: "accepted"|"rejected"}
POST   /api/videos/:id/export   → returns download URL (CSV/JSON)
```

## Decisons Made

- Branch strategy: `main` (default) + `issue/N` feature branches. No `master`.
- Preview deployments on every PR via `preview.yml`
- Backend and frontend in same monorepo (`/frontend`, `/backend` dirs)
- SQLite for dev, PostgreSQL for prod (via SQLAlchemy Alembic migrations)
