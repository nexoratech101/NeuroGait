# NeuroGait Platform

Server-side companion to the NeuroGait Alert System wearable: a FastAPI backend
and React dashboard for reviewing MS gait assessments recorded by up to three
IMU sensors (ankle / thigh / hip).

**Status:** research prototype, graduate research project (Western University).
Not a regulated medical device. **No diagnostic or prognostic claims are made
anywhere in this system** -- every string in the UI, every report template,
and every API field is written as a neutral, descriptive, comparative
statement (e.g. "walking speed decreased by 8% vs previous assessment", never
"MS is progressing").

This directory (`platform/`) is deliberately separate from the Arduino
firmware (`../firmware`) and Flutter mobile app (`../lib`) that live elsewhere
in this repository -- it is a standalone backend + web dashboard.

## Quick start

```bash
cd platform
docker compose up --build
```

- Backend API: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173
- Postgres: localhost:5432 (user/pass/db: `neurogait`)

Seed a demo patient + demo session (built from a synthetic sample CSV that
mimics the real sensor file's characteristics -- ~50 Hz, ~4 min, single
sensor, no filename metadata):

```bash
docker compose exec backend python -m app.seed
```

Then log in at http://localhost:5173 with:

- `admin@neurogait.example.com` / `changeme123` (admin)
- `physician@neurogait.example.com` / `changeme123` (physician)

## Running tests

```bash
cd platform/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Tests run against an isolated SQLite database (no Postgres required) and
include an end-to-end flow: upload a legacy (no-metadata) sample file ->
prompt for manual patient association -> create new patient -> pipeline runs
in the background -> dashboard data + PDF report are retrievable.

## The measured / estimated / derived convention

Every gait metric returned by the API and shown in the UI carries a status
tag:

- **measured** -- computed directly from sensor timing/events (cadence, step
  time, stride time).
- **derived** -- computed from measured values via a defined calculation
  (gait regularity index, an autocorrelation-based score).
- **estimated** -- produced by a model that has not been validated in this
  phase (walking speed, stride length). These are never shown in the core
  dashboard summary; they sit behind a "research metrics" toggle and are
  always rendered with the `estimated` tag visible.

No value is ever displayed without its tag. This is enforced end-to-end: the
DB schema carries a `*_status` column next to metrics that need one, the API
wraps every metric in `{value, status, unit}`, and the frontend's
`MetricTile` component always renders the tag.

## Signal processing pipeline

Each stage lives as an independently testable pure function under
`backend/app/pipeline/`:

1. `file_validator` -- required columns present, parseable, non-empty
2. `metadata_extractor` -- parses `PAT-..._SES-..._POS-..._DEV-...csv`, or
   flags the file as legacy/no-metadata
3. `patient_association` -- matches filename metadata to an existing patient,
   or signals manual selection/creation is needed (the router does the DB
   lookup; this module is the pure matching logic)
4. `qc` -- per-sensor QC: sampling-rate estimate, gap detection/locations,
   duplicate timestamps, saturation, range sanity
5. `position_plausibility` -- accel-variance heuristic vs. claimed position;
   WARNING only, never a hard rejection
6. `filtering` -- Butterworth low-pass (~20 Hz) / optional high-pass (~0.5 Hz)
7. `gravity_compensation` -- estimates gravity from the quietest window in
   the recording and removes it
8. `motion_signal` -- vector magnitude of the dynamic (gravity-removed) accel
9. `bout_detection` -- windowed energy threshold (Otsu's method on
   1-second-window variance) + minimum 5s bout duration
10. `event_detection` -- peak detection on the motion signal, per bout
11. `segmentation` -- pairs events into steps and strides
12. `features` -- cadence, step/stride time + CV, autocorrelation-based
    regularity index -- **the Phase 1 metric floor, computable from one
    sensor** (hip preferred; any single sensor works)
13. `quality` -- combines all QC signals into a 0-100 Data Quality Score with
    plain-language reasons
14. `clinical_metrics` -- packages outputs, tags each measured/estimated/derived
15. `trend` -- compares current session to previous and to the first
    ("baseline") session for the patient; absolute + percentage change,
    neutral language only
16. `report_generator` -- populates the PDF report (WeasyPrint), including
    the mandatory limitations footer

`pipeline_runner.py` orchestrates stages 4-14 for a single recording;
`pipeline_service.py` bridges that pure pipeline to the database and is
invoked via FastAPI `BackgroundTasks` after upload/association.

Raw uploaded files are **never modified**: each is hashed (SHA-256) and
stored under `/data/raw/<session_id>/`, addressable independently of any
processed output in `/data/processed/`. Every `gait_analysis` row records the
`algorithm_version` (== `processing_version` on the session) so results stay
reproducible from the raw file at any later date.

## Phase 1 vs. Future placeholders

**Phase 1 (built now):** auth/roles, patient records, 1-3 sensor session
upload with per-sensor QC, single-sensor gait pipeline (cadence, step/stride
time + CV, regularity index), Data Quality Score, session dashboard,
baseline/previous comparison, clinical notes, PDF report, audit log, raw-file
traceability.

**Future placeholders (Phase 2+, not built)** -- represented as either a
disabled UI element, a stub returning `null`/"not yet available", or a
present-but-unused schema field, never silently missing:

| Item | Where it shows up now |
|---|---|
| WhatsApp Business API auto-ingestion | Manual upload only in Phase 1 |
| Multi-sensor time sync beyond nearest-timestamp interpolation | Core metrics computed from one preferred sensor only |
| Bilateral asymmetry | `gait_asymmetry_pct` column exists, always `null`; hidden in UI |
| Turning analysis | `turning_metrics` JSONB column exists, returns `{"status": "not_yet_available"}`; nav item disabled |
| Fatigue analysis | `fatigue_metrics` JSONB column exists, same pattern; nav item disabled |
| Movement smoothness | `movement_smoothness` column exists, always `null` |
| AI/ML anything (event detection via ML, fall-risk, anomaly detection) | Not present |
| Alerts/thresholds engine | Not present |
| Research-mode cohort tools, anonymized export, algorithm-version comparison | Nav item disabled |
| Patient-facing portal/app | Not present |
| Normative/reference-population comparison | Not present |
| Multi-clinic/tenant management, billing | Not present |
| REB/consent enforcement logic | `patients.consent_recorded` boolean field exists, shown as a notice banner in the UI when false, but nothing blocks on it |

## Open decisions carried over from the spec

These don't block Phase 1 but should be confirmed before Phase 2 work
(asymmetry, turning) begins:

1. Bilateral vs. unilateral sensor placement -- Phase 1 assumes unilateral.
2. Real-time multi-sensor BLE streaming vs. local-log-then-sync -- Phase 1
   assumes local-log-then-sync.
3. Sensor units (accel in g, gyro in deg/s) -- assumed from the sample
   fixture's value ranges, **not yet verified against firmware**. See
   `SENSOR_UNITS_VERIFIED = False` in `backend/app/config.py`.

## Stack

FastAPI (Python 3.11) · PostgreSQL 16 · NumPy/SciPy/pandas · FastAPI
`BackgroundTasks` (no Celery/Redis in Phase 1) · React + Vite · Recharts ·
WeasyPrint · JWT auth via `python-jose` + `passlib`/bcrypt · Docker Compose.
All open-source, no paid APIs or cloud services assumed.

## API surface

See `backend/app/routers/` for the full implementation. Summary:

```
POST   /auth/login
POST   /auth/logout
GET    /patients
POST   /patients
GET    /patients/{id}
PATCH  /patients/{id}
GET    /patients/{id}/sessions
GET    /patients/{id}/trend
POST   /sessions/upload
POST   /sessions/{id}/associate
GET    /sessions/{id}
GET    /sessions/{id}/status
GET    /sessions/{id}/analysis
GET    /sessions/{id}/quality
GET    /sessions/{id}/raw/{recording_id}
POST   /sessions/{id}/notes
GET    /sessions/{id}/notes
POST   /sessions/{id}/report
GET    /sessions/{id}/report
GET    /sessions/{id}/report/download
GET    /audit-log            (admin only)
```
