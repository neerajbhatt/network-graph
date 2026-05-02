# CLAUDE.md — Network Graph

## Project Overview
**Network Graph** is a pharmacy fraud & abuse detection platform that surfaces suspicious networks (doctor shopping, prescriber-pharmacy collusion, pharmacy hubs, geo-anomalies) in pharmacy claims for controlled and commonly-abused drugs.

## Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, pandas, numpy
- **Frontend**: React 18, Vite, Tailwind CSS, TypeScript (strict mode)
- **Database**: PostgreSQL 15 (schema: `network_graph`)
- **Data**: Synthetic mode (`DATA_MODE=SYNTHETIC`) with 10K members, 500 prescribers, 200 pharmacies, ~29K pharmacy claims, ~5% planted fraud
- **Deployment**: Render.com (render.yaml blueprint), Docker Compose for local

## Repo Structure
```
backend/
  network_graph_core/          # Reusable detection package
    detectors/                 # 5 detector modules (pure functions: df + config -> df)
      suspicious_fills.py      # R1: No medical/dental visit within lookback
      network_buckets.py       # R2: Prescriber-pharmacy shared member count
      doctor_shopping.py       # R4.2: Members at multiple pharmacies/prescribers
      pharmacy_hubs.py         # R4.3: Pharmacies with many prescribers
      geo_anomaly.py           # R6: Haversine distance outliers
    config.py                  # DetectionConfig dataclass, loaded from CONFIG_DETECTION_RULES
    synthetic.py               # Faker+numpy data generator, seeded for reproducibility
  api/
    main.py                    # FastAPI app, all endpoints under /api/network-graph/
    models.py                  # Pydantic response models
    database.py                # SQLAlchemy connection, query_df(), execute()
  sql/
    ddl/                       # 5 DDL files (schema, dims, facts, detection, views)
    seed/                      # Config rules + 58 NDCs for REF_CONTROLLED_DRUGS
    procs/                     # 5 SQL stored procedures mirroring Python detectors
  tests/                       # 26 unit tests, pytest
  load_data.py                 # CSV -> Postgres loader
  run_detections.py            # Runs all detectors, writes to fact_suspicious_fill + audit log
frontend/
  src/pages/                   # 5 tabs: Networks, DoctorShoppers, PharmacyHubs, GeoOutliers, Config
  src/components/              # KpiCards, RiskBadge
  src/lib/api.ts               # API client with typed interfaces
```

## Key Commands
```bash
make install          # Install backend + frontend deps
make seed             # Generate synthetic data + load into Postgres
make detect           # Run all detection algorithms
make api              # Start FastAPI on :8000
make web              # Start Vite dev server on :3000
make demo             # Full stack: db + seed + detect + api + web
make test             # pytest with coverage
make smoke            # Hit all API endpoints, assert non-empty
make lint             # ruff + mypy (backend), eslint + tsc (frontend)
docker compose up     # Full stack via Docker
```

## API Endpoints (all under /api/network-graph/)
- `GET /healthz` — health check
- `GET /kpi` — KPI summary (claims, exposure, members, flagged)
- `GET /networks` — force graph nodes+edges (filters: bucket, drug_class, state, specialty, from, to, min_shared)
- `GET /networks/{id}/drill` — drill into prescriber/pharmacy node
- `GET /doctor-shoppers` — paginated (filters: min_pharmacies, min_prescribers, from, to)
- `GET /pharmacy-hubs` — paginated (filter: min_prescribers)
- `GET /geo-outliers` — paginated (filter: min_miles)
- `GET /config/rules` + `PUT /config/rules` — detection thresholds

## Detection Thresholds (in CONFIG_DETECTION_RULES table, never hardcoded)
- Suspicious fills lookback: 30 days default (45 for gabapentinoids)
- Network buckets: HIGH > 60, MEDIUM > 20 shared members
- Doctor shopping: >= 3 pharmacies or >= 3 prescribers
- Pharmacy hubs: >= 5 distinct prescribers
- Geo anomaly: > 50 miles absolute or > 95th percentile of member history

## Database Schema
Star schema in `network_graph` schema: DIM_MEMBER, DIM_PRESCRIBER, DIM_PHARMACY, DIM_DRUG, FACT_PHARMACY_CLAIM, FACT_MEDICAL_CLAIM, FACT_DENTAL_CLAIM, FACT_SUSPICIOUS_FILL, REF_CONTROLLED_DRUGS, CONFIG_DETECTION_RULES, AUDIT_DETECTION_RUNS. Four reporting views: RPT_NETWORK_BUCKETS, RPT_DOCTOR_SHOPPERS, RPT_PHARMACY_HUBS, RPT_GEO_OUTLIERS.

## Design Patterns
- Detectors are **pure functions**: `detect(dataframe, config) -> dataframe` — no DB coupling
- All thresholds live in `CONFIG_DETECTION_RULES`, exposed via Config tab + API
- Every detection run logs to `AUDIT_DETECTION_RUNS`
- PHI fields (`member_name`, `dob`, `address`) marked with `# PHI` comments
- `DATA_MODE` env var switches between SYNTHETIC and REAL data paths

## Linting & Testing
- Backend: `ruff check` (line-length 120) + `mypy --strict` + `pytest` (26 tests, all passing)
- Frontend: `eslint` + `tsc --strict` + `vite build` (all clean)
- Detector tests validate recall >= 0.9 on planted fraud patterns

## Deployment
- **GitHub**: https://github.com/neerajbhatt/network-graph
- **Render**: render.yaml blueprint (Postgres free tier + Python web service + static site)
- **Docker**: `docker compose up --build` for local full-stack

## Important Files
- `DECISIONS.md` — 18 architectural decisions with rationale
- `OPEN_QUESTIONS.md` — 10 items for human review
- `docs/architecture.md` — Mermaid ERD
- `docs/powerbi.md` — RPT_* view docs + DAX measures
