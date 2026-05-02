# Network Graph — One-Shot Build Prompt

> **Project**: Network Graph — Pharmacy Fraud & Abuse Detection Platform
> **Mode**: Single-shot end-to-end build. No phase gates.

Copy the section below the line into Claude Code as your build prompt. Above the line is guidance for *you* on how to use it.

---

## How to use this prompt

1. Drop into Claude Code at the root of a fresh repo named `network-graph`.
2. **Replace placeholders before running:**
   - `<DB_ENGINE>` → `Snowflake` / `Postgres` / `SQL Server` (Postgres recommended for fastest local demo)
   - `<LOOKBACK_DAYS_DEFAULT>` → `30`
   - `<HIGH_THRESHOLD>` → `60`
   - `<MEDIUM_THRESHOLD>` → `20`
3. Expect the build to run for a while. Let it finish without interruption.
4. After it completes, run `make demo` (or the documented start command). Then do a review pass on `DECISIONS.md`, the ERD, and the detection logic before showing it to anyone.

---

# 🟦 BUILD PROMPT — Network Graph (one-shot, end-to-end)

## Role
You are a senior healthcare data engineer and full-stack developer. Build **Network Graph** — a production-grade pharmacy fraud and abuse detection platform — end-to-end in this session. Do not stop for confirmation between phases. Make sensible architectural decisions when requirements are ambiguous and document them in `DECISIONS.md`. Only stop to ask if a decision would meaningfully change scope or break the build.

## Business Problem
Detect potential fraud, abuse, or misuse in pharmacy claims for **controlled and commonly-abused drugs**, specifically when members receive these drugs **without a supporting physician or dental visit** within a configurable lookback window. Surface suspicious networks (doctor shopping, prescriber–pharmacy collusion, pharmacy hubs, geo-anomalies) that current analytics miss.

## Primary Users
- **SIU analysts** — drill into prescriber-pharmacy-member-drug combinations
- **Clinical fraud reviewers** — validate flagged cases
- **Leadership** — Power BI / dashboard summary of risk buckets, $ exposure

## Environment
- Project name: **Network Graph**
- Repo name: `network-graph`
- Database: `<DB_ENGINE>` (default: Postgres for local demo speed)
- Schema: `NETWORK_GRAPH`
- Backend: Python 3.11, FastAPI
- Frontend: React + Vite + Tailwind, Recharts for charts, react-force-graph for network views, react-leaflet for maps
- Data mode: `SYNTHETIC` only for v1 (with a clean switch point for `REAL` later)
- Power BI compatibility: clean star-schema reporting views

## Core Requirements

### R1 — Suspicious Pharmacy Claims
Flag pharmacy claims for controlled/abused drugs where the member has **no medical or dental visit** within `<LOOKBACK_DAYS_DEFAULT>` days before the fill date. Lookback is configurable per drug class.

### R2 — Prescriber–Pharmacy Network Detection
Build a graph of prescribers and pharmacies linked by shared members. Bucket by shared-member count:
- **HIGH**: > `<HIGH_THRESHOLD>` (default 60)
- **MEDIUM**: `<MEDIUM_THRESHOLD>` < x ≤ `<HIGH_THRESHOLD>` (default 20–60)
- **LOW**: ≤ `<MEDIUM_THRESHOLD>`

Thresholds live in `CONFIG_DETECTION_RULES`, never hardcoded.

### R3 — Drill-Down
Any network node → prescriber → pharmacy → member → drug (NDC + name + days supply + fill date + claim $).

### R4 — Multi-Perspective Analysis
Three lenses, each its own API endpoint and dashboard tab:
1. **Prescriber–Pharmacy networks** (R2)
2. **Member doctor-shopping** — members filling at ≥ N pharmacies or seeing ≥ N prescribers in the lookback
3. **Pharmacy-centric** — pharmacies receiving from ≥ N distinct prescribers for the same member cohort

### R5 — Filtering & Visualization
Network views filter by: drug class, date range, bucket, geography (state/zip), prescriber specialty. Edge weight = shared-member count. Allow collapsing low-weight edges.

### R6 — Geo-Distance Anomaly
Haversine distance between member home zip centroid and pharmacy zip centroid. Flag fills where distance > 95th percentile of the member's history OR > absolute threshold (default 50 miles, configurable).

### R7 — Reference Data
`REF_CONTROLLED_DRUGS` keyed on NDC with drug-name fallback. Seed with DEA Schedule II–V plus commonly abused drugs (opioids, benzos, stimulants, gabapentinoids, muscle relaxants). Columns: `drug_class`, `dea_schedule`, `is_controlled`, `is_commonly_abused`.

### R8 — Reporting Tables
- **Detail**: `FACT_SUSPICIOUS_FILL` — one row per flagged claim, all dimension keys
- **Summary**: `RPT_NETWORK_BUCKETS`, `RPT_DOCTOR_SHOPPERS`, `RPT_PHARMACY_HUBS`, `RPT_GEO_OUTLIERS`

Power BI-friendly: flat, denormalized where helpful, no nested types.

### R9 — Configurable Lookback
Per-drug-class lookback in `CONFIG_DETECTION_RULES` (default 30 days).

### R10 — Reusable Core
Detection logic in a Python package `network_graph_core/` with clear interfaces, so future fraud domains (DME, lab) can plug in.

## Deliverables — build all of these in this single session

### 1. Foundation
- `DECISIONS.md` — every architectural choice and assumption, with rationale
- `OPEN_QUESTIONS.md` — anything left for human review
- `README.md` — setup, run, demo instructions, switching to REAL data mode
- `docs/architecture.md` — mermaid ERD covering: `DIM_MEMBER`, `DIM_PRESCRIBER`, `DIM_PHARMACY`, `DIM_DRUG`, `FACT_PHARMACY_CLAIM`, `FACT_MEDICAL_CLAIM`, `FACT_DENTAL_CLAIM`, `FACT_SUSPICIOUS_FILL`, `REF_CONTROLLED_DRUGS`, `CONFIG_DETECTION_RULES`, `AUDIT_DETECTION_RUNS`, the four `RPT_*` views
- Repo skeleton:
  ```
  network-graph/
  ├── backend/
  │   ├── network_graph_core/      # reusable detection package
  │   │   ├── detectors/
  │   │   ├── synthetic.py
  │   │   └── config.py
  │   ├── api/                     # FastAPI app
  │   ├── sql/
  │   │   ├── ddl/
  │   │   ├── seed/
  │   │   └── procs/
  │   └── tests/
  ├── frontend/
  │   └── src/
  │       ├── components/
  │       ├── pages/
  │       └── lib/
  ├── data/synthetic/
  ├── docs/
  ├── Makefile
  └── docker-compose.yml
  ```

### 2. Data Layer
- DDL for all tables in `<DB_ENGINE>` dialect with indexes on join keys
- Synthetic generator (`network_graph_core/synthetic.py`):
  - 10,000 members, 500 prescribers, 200 pharmacies, 6 months of claims
  - ~5% planted fraud patterns: doctor shoppers, collusive prescriber-pharmacy pairs, geo-outliers
  - Faker + numpy, seeded for reproducibility
- Seed `REF_CONTROLLED_DRUGS` with at least 50 real NDC examples across drug classes
- Loader scripts wired into a `make seed` command

### 3. Detection Engine
Pure functions in `network_graph_core/detectors/`:
- `suspicious_fills.py` (R1)
- `network_buckets.py` (R2)
- `doctor_shopping.py` (R4.2)
- `pharmacy_hubs.py` (R4.3)
- `geo_anomaly.py` (R6) — ship a small zip→lat/lon parquet lookup

Each detector accepts a config object, returns a typed DataFrame with documented schema. Unit tests with planted-pattern data validating recall ≥ 0.9.

Equivalent SQL stored procs in `backend/sql/procs/` for warehouse-side execution.

### 4. API
FastAPI under `/api/network-graph/`:
- `GET /networks?bucket=&drug_class=&from=&to=` → nodes + edges
- `GET /networks/{network_id}/drill`
- `GET /doctor-shoppers?min_pharmacies=&from=&to=`
- `GET /pharmacy-hubs?min_prescribers=`
- `GET /geo-outliers?min_miles=`
- `GET /config/rules` and `PUT /config/rules`
- `GET /healthz`

OpenAPI auto-generated. Pydantic response models. Pagination on all list endpoints.

### 5. Frontend
Header: "Network Graph". Dark theme, Tailwind + shadcn-style components. Five tabs:
1. **Networks** — force-directed graph (react-force-graph), node = prescriber/pharmacy, edge weight = shared members, color by bucket; click node → drill panel; left-rail filters
2. **Doctor Shoppers** — sortable table + member detail drawer with timeline of fills
3. **Pharmacy Hubs** — table + bar chart of top hubs by distinct prescriber count
4. **Geo Outliers** — react-leaflet map with home-to-pharmacy lines colored by distance bucket
5. **Config** — edit thresholds + lookback, save hits `PUT /config/rules`

KPI cards on every tab: claim count, $ exposure, member count.

### 6. Power BI Hand-off
- `docs/powerbi.md` documenting `RPT_*` views
- Sample DAX measures for $ exposure, member count, bucket distribution
- Verify views are flat with no nested types

### 7. Demo Glue
- `Makefile` with: `make install`, `make seed`, `make api`, `make web`, `make demo` (full stack up)
- `docker-compose.yml` for db + api + web
- Smoke test script that hits every endpoint and asserts non-empty results
- README's quickstart must work on Windows Git Bash and macOS

## Non-Functional Requirements
- PHI fields (`member_id`, `member_name`, `dob`, `address`) marked `# PHI` and excluded from logs
- Every detection run logs to `AUDIT_DETECTION_RUNS`: rule_id, rule_version, run_timestamp, input_count, flagged_count
- Unit test coverage ≥ 80% on `network_graph_core`
- All thresholds in `CONFIG_DETECTION_RULES`
- Backend passes `ruff` + `mypy --strict`. Frontend passes `eslint` + `tsc --strict`

## Working Style for This Session
- Build straight through. Do not stop between sections for confirmation.
- Document every nontrivial decision in `DECISIONS.md` as you make it.
- Anything truly ambiguous → log to `OPEN_QUESTIONS.md` and proceed with the most defensible default.
- Prefer boring, proven libraries.
- No stubs in production paths. Anything unimplemented raises `NotImplementedError` with a clear message.
- After the build is complete, run the smoke test and report the results in your final message.

## Definition of Done
- `make demo` brings up DB + seeded synthetic data + API + frontend
- All five frontend tabs render real data with planted fraud patterns visibly surfaced
- Smoke test passes
- All four `RPT_*` views queryable from Power BI Desktop
- README quickstart works from a clean clone

## Final Output Required
At the end of the session, post a single summary message containing:
1. ✅/❌ status of each deliverable
2. Smoke test output
3. The exact commands to run the demo
4. Top 3 items in `OPEN_QUESTIONS.md` for me to review
