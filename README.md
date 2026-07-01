# PlacementIQ

**ML-Powered Eligibility Predictor and Analyzer**

A full-stack student management and analytics platform for training-centre environments (CDAC-style course structure). It covers student master data, multi-category assessments, bulk Excel ingestion, SQL-driven analytics views, in-app placement reporting, optional Power BI embedding, and ML-assisted placement prediction.

---

## System Architecture

Containerized with Docker Compose:

| Service | Stack | Role |
|---------|-------|------|
| **Frontend** | Next.js 15 (App Router), Tailwind, Recharts | Role-based UI; NextAuth.js sessions |
| **Backend** | Django 5 + DRF | Auth (JWT), RBAC, CRUD, bulk import, reports |
| **ML Service** | FastAPI | Risk/placement prediction; live metrics WebSocket |
| **Database** | PostgreSQL 16 | System of record + analytics SQL views |
| **Redis** | Redis 7 | Celery broker / cache |
| **Celery** | Worker + Beat | Infrastructure present; Beat schedule disabled by default; bulk import runs synchronously in the API |
| **Nginx** | Reverse proxy | Production routing / SSL |

---

## Core Concepts

### PRN (Permanent Registration Number)

- **What**: Unique 12-digit student identifier (primary key of `student_master`).
- **Used for**: Linking scores, user accounts (`users_user.prn`), analytics views, and ML features.
- **Example**: `24020128001`

### TPRN (Test Permanent Registration Number)

- **What**: Unique identifier for a registered sub-test in `sub_tests`.
- **Format**: `{CATEGORY_CODE}-{SEQ}` with a zero-padded 3-digit sequence.
- **Examples**: `AP-001`, `CC-003`, `IA-008`
- **Auto-generation**: When an admin or HOD creates a sub-test via API/UI, `generate_tprn()` in `backend/apps/assessments/viewsets.py` assigns the next sequence for that category (respecting `main_categories.no_of_subtests`).

**How TPRN fits in the workflow**

1. **Register category** — `main_categories` defines codes such as `CC`, `IA`, `AP`, `SX`, `PS`, `GR`, `TA`, `NA`, `IN`, `AS`, `PQ`, `GAC`, `PRJ`, each with `scaled_marks` and `no_of_subtests`.
2. **Register sub-test** — Admin/HOD creates a `sub_tests` row scoped to `centre_code`, `course_code`, `batch_name`, and `category_code`. The backend assigns `tprn` automatically; you do not invent TPRNs manually unless importing via bulk sub-test upload.
3. **Map tests to Excel columns (matrix marks)** — For horizontal score tables (`scores_cc`, `scores_ia`, etc.), `test_mapping` links a batch + category to logical test names and column slots (`test_01` … `test_20`). Marks bulk upload uses these mappings, not raw TPRN columns.
4. **Legacy path** — `student_test_scores` still exists for read-only compatibility; **canonical writes** go to `scores_*` tables.

**Rule**: A sub-test (TPRN) or test mapping must exist before marks for that test can be stored.

### Batch management

- Batches are lookup rows in `batches` with `batch_month` **`02`** (February) or **`08`** (August) and a display label such as `Feb 2024` / `Feb/24`.
- Students reference a batch via `student_master.batch_id` (FK to `batches.batch_name`).

### Assessment & mark scaling

- Raw sub-test scores are aggregated per category and scaled to each category’s `scaled_marks`.
- Category scaled totals sum to a **1500-mark grand total** (see `v_student_grand_total` and `grade_scale`).
- Placement cutoffs and status are computed in `v_placement_report` (`Placement ready`, `Can Improve`, `Not Placement ready`).

---

## Roles & UI routes

| Role | Access |
|------|--------|
| **admin** | Full access: master data, bulk import, users, placement report, model training, Power BI |
| **hod** | Course-scoped (`hod_courses`); placement report, marks + test management, Power BI |
| **faculty** | Marks management at `/admin/data-management?tab=marks`; Power BI |
| **student** | Own dashboard, scores, and Power BI **My Marks** view (RLS-scoped) |
| **All roles** | Account settings at `/settings` |

**Frontend routes (examples)**

- `/admin/dashboard`, `/admin/students`, `/admin/data-management`, `/admin/placement-report`, `/admin/power-bi`, `/admin/model-training`
- `/hod/dashboard`, `/hod/placement-report`, `/hod/power-bi`
- `/faculty/dashboard`, `/faculty/power-bi`, `/admin/data-management?tab=marks`
- `/student/dashboard`, `/student/scores`, `/student/power-bi` (My Marks)

---

## Technology Stack

**Frontend**: Next.js 15, NextAuth.js, Tailwind CSS, Framer Motion, Recharts, Lucide  
**Backend**: Django 5, DRF, SimpleJWT, PostgreSQL 16, Celery, Redis  
**ML**: FastAPI, scikit-learn artifacts under `ml_service/artifacts/`  
**Reporting**: In-app placement/CCEE-IA reports + optional Power BI embed (`CDAC.pbix`)

---

## Key Features

- Admin dashboard with live KPIs
- Bulk Excel import (students, sub-tests, test mappings, marks matrix)
- Horizontal `scores_*` storage per assessment category
- Placement report with Final Grade, module rankings (M4/M6/M8), rules-based status + ML override when `ml_service` is healthy
- Analytics API backed by PostgreSQL views
- Optional Power BI embed (requires Azure AD app + Embedded/Premium capacity)
- Audit logging for compliance
- JWT auth with role-based API permissions

---

## Setup & Installation

### Prerequisites

- Docker & Docker Compose (recommended), or Python 3.11+, Node.js 18+, PostgreSQL 16, Redis 7

### Environment

Copy and edit `.env` at the repository root (used by `docker-compose.yml`). Key groups:

- `POSTGRES_*`, `DJANGO_*`, `REDIS_*`, `CELERY_*`
- `NEXT_PUBLIC_API_URL` for the frontend
- Optional Power BI embed: `POWERBI_CLIENT_ID`, `POWERBI_TENANT_ID`, `POWERBI_CLIENT_SECRET`, `POWERBI_WORKSPACE_ID`, `POWERBI_REPORT_ID`, `POWERBI_ENABLE_RLS=false`

### Docker (recommended)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| ML Service | http://localhost:8001 |
| Flower | http://localhost:5555 |
| Nginx | http://localhost:80 |

### Local development

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Apply analytics views** (after DB is up):

```bash
psql -U <user> -d <db> -f backend/POSTGRESQL_ANALYTICS_VIEWS.sql
```

---

## Project Structure

```
Student_Dashboard/
├── frontend/                 # Next.js app (app/, components/, lib/)
├── backend/
│   ├── config/               # Settings, URLs, permissions
│   ├── apps/
│   │   ├── users/            # User model, JWT profile, bulk user upload
│   │   ├── assessments/      # Master data, scores_*, bulk upload, placement API
│   │   ├── analytics/        # Read-only view models, audit log
│   │   └── powerbi/          # Embed token API
│   ├── POSTGRESQL_ANALYTICS_VIEWS.sql
│   └── manage.py
├── ml_service/                 # FastAPI prediction service
├── Docs/                       # Architecture specs, generated CDAC_SRS.docx
├── docker-compose.yml
├── report.js                   # Generates Docs/CDAC_SRS.docx (npm run generate:srs)
└── CDAC.pbix                   # Power BI report (cloud-connected)
```

---

## Database Overview

### Master data

- `centres`, `courses`, `batches` — lookup tables
- `student_master` — students (PK: `prn`)
- `main_categories` — assessment types (`category_code`, `scaled_marks`, `no_of_subtests`)
- `sub_tests` — registered tests (PK: `tprn`, FKs to centre/course/batch/category)
- `test_mapping` — batch + category → logical name + `column_slot` for matrix marks

### Score storage (canonical)

Horizontal tables, one row per student per category:

`scores_cc`, `scores_ia`, `scores_ap`, `scores_sx`, `scores_ps`, `scores_gr`, `scores_ta`, `scores_na`, `scores_in`, `scores_as`, `scores_pq`, `scores_gac`, `scores_prj`

Each holds `test_01` … `test_20` columns populated from the marks matrix import or the marks UI.

`student_test_scores` — legacy read-only; do not use as the primary write target.

### Analytics views (read-only)

Defined in `backend/POSTGRESQL_ANALYTICS_VIEWS.sql`, consumed by Django `analytics` models and reports:

| View | Purpose |
|------|---------|
| `v_student_category_scores` | Per-student per-category scaled scores |
| `v_student_grand_total` | 1500-mark total + grade |
| `v_student_scores_by_date` | Chronological score history |
| `v_exam_schedule_with_dates` | Calendar / upcoming exams |
| `v_monthly_activity_breakdown` | Monthly participation |
| `v_placement_report` | Full placement report + `placement_status` |
| `v_ccee_ia_modules` | CCEE/IA module breakdown and ranks |
| `v_batch_percentile`, `v_spider_chart_data`, `v_category_ranking`, … | Extended analytics |

---

## Data Ingestion Flow

Recommended order:

1. **Centres, courses, batches** — via admin API or UI (`/api/assessments/centres/`, etc.)
2. **Students** — `POST /api/assessments/bulk-upload/student-master/` (Excel: `prn`, `student_full_name`, centre/course/batch names)
3. **Sub-tests** — UI/API (`POST /api/assessments/subtests/`) auto-assigns TPRN, or `POST /api/assessments/bulk-upload/subtests/`
4. **Test mappings** — `POST /api/assessments/bulk-upload/test-mappings/` (required for matrix marks layout)
5. **Marks** — `POST /api/assessments/bulk-upload/marks/` → writes to `scores_*` tables
6. **Staff users** — `POST /api/users/bulk/users_upload/` (admin only)

Marks management UI: `/admin/data-management` (admin, faculty, HOD per permissions).

---

## API Reference (main endpoints)

### Authentication

- `POST /api/token/` — obtain JWT access + refresh (SimpleJWT)
- `POST /api/token/refresh/` — refresh access token  
- Frontend uses **NextAuth.js** credentials provider; there is no custom `/api/auth/logout/` on the backend.

### Assessments

- `GET/POST /api/assessments/centres/`, `courses/`, `batches/`, `main-categories/`
- `GET/POST /api/assessments/subtests/` — create sub-test (**TPRN auto-generated**)
- `GET/POST /api/assessments/student-master/`
- `GET/POST /api/assessments/test-mappings/`
- `GET /api/assessments/test-scores/` — read-only legacy scores
- `GET/PUT /api/assessments/scores/<category_code>/<prn>/` — horizontal score read/write
- `GET /api/assessments/reports/placement/` — placement report (staff)
- `GET /api/assessments/reports/ccee-ia-modules/` — CCEE/IA module report

### Bulk upload (admin)

- `POST /api/assessments/bulk-upload/student-master/`
- `POST /api/assessments/bulk-upload/subtests/`
- `POST /api/assessments/bulk-upload/test-mappings/`
- `POST /api/assessments/bulk-upload/marks/`
- `POST /api/users/bulk/users_upload/`

### Analytics

- `GET /api/analytics/student_summary/?prn=`
- `GET /api/analytics/system_overview/`
- `GET /api/analytics/role-dashboard/`
- `GET /api/analytics/grand-totals/`
- `GET /api/analytics/category-scores/`
- `GET /api/analytics/scores-by-date/`
- `GET /api/analytics/monthly-activity/`
- `GET /api/analytics/audit-logs/`

### ML service (port 8001)

- `GET /health`
- `GET /ml/predict-risk/{prn}`
- `POST /ml/predict-placement/`
- `POST /ml/predict-bulk/`
- `POST /ml/train/`, `GET /ml/training-status/`
- `WebSocket /ws/live-metrics`

### Power BI (admin, HOD, faculty, student)

- `GET /api/powerbi/embed-config/` — returns embed token when `POWERBI_*` env vars and capacity are configured

---

## Power BI

- **Desktop/Service**: Open `CDAC.pbix` directly for authoring and refresh against PostgreSQL.
- **In-app embed**: `/admin/power-bi`, `/hod/power-bi`, `/faculty/power-bi`, or `/student/power-bi` (My Marks, student RLS) — works when Azure AD + Power BI Embedded (or eligible Premium) is configured; otherwise shows setup instructions.
- **Refresh tip**: If `placement_status` errors on refresh, re-apply `POSTGRESQL_ANALYTICS_VIEWS.sql` and set the column type to **Text** in Power Query.

---

## Administrative credentials

Default dev credentials (if seeded): check your `.env` / seed scripts. Create a superuser:

```bash
cd backend
python manage.py createsuperuser
```

Rotate default passwords before any non-development deployment.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Docs/student_analytics_master.md](./Docs/student_analytics_master.md) | Consolidated functional/technical spec |
| [Docs/postgres_student_analytics_architecture_v6.md](./Docs/postgres_student_analytics_architecture_v6.md) | PRN architecture reference |
| [Docs/student_analytics_postgres_architecture.md](./Docs/student_analytics_postgres_architecture.md) | PostgreSQL design notes |
| [backend/OPS.md](./backend/OPS.md) | Backend operational runbook |
| [Docs/CDAC_SRS.docx](./Docs/CDAC_SRS.docx) | SRS (generate with `npm run generate:srs`) |
| [ml_service/README.md](./ml_service/README.md) | ML training and prediction |

---

## Generate SRS document

```bash
npm install          # root package.json (docx dependency)
npm run generate:srs # writes Docs/CDAC_SRS.docx
```

---

*PlacementIQ — ML-Powered Eligibility Predictor and Analyzer*
