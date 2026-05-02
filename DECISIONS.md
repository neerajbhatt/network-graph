# Architectural Decisions — Network Graph

## D1 — Database: PostgreSQL
**Choice**: Postgres 15+ for local development and demo.
**Rationale**: Fastest local setup, excellent JSON/array support, strong geospatial (PostGIS not needed — Haversine in Python), free. Production migration to Snowflake requires only DDL dialect changes and swapping the connection layer.

## D2 — Schema Name: `network_graph`
**Choice**: All tables live in `network_graph` schema.
**Rationale**: Namespace isolation; avoids collisions with other analytics schemas.

## D3 — Synthetic Data Mode Toggle
**Choice**: `DATA_MODE` env var (`SYNTHETIC` | `REAL`). Synthetic generator only runs when `DATA_MODE=SYNTHETIC`. Real-data path expects pre-loaded tables matching the same DDL.
**Rationale**: Clean switch point without code changes. Real data ETL is out of scope for v1.

## D4 — Detection Engine as Pure Functions
**Choice**: Detectors accept DataFrames + config, return DataFrames. No DB coupling inside detectors.
**Rationale**: Testable, reusable across future fraud domains (DME, lab). DB I/O stays in the API/ETL layer.

## D5 — Thresholds in CONFIG_DETECTION_RULES Table
**Choice**: All detection thresholds stored in `config_detection_rules` with `rule_name`, `parameter_name`, `parameter_value` columns. Never hardcoded.
**Rationale**: SIU analysts can tune thresholds without code deploys. API exposes GET/PUT for the config tab.

## D6 — Lookback Window: 30 Days Default
**Choice**: Default lookback is 30 days. Configurable per drug class in `config_detection_rules`.
**Rationale**: 30 days balances sensitivity (catching fills without recent visits) vs. specificity (avoiding false positives from routine follow-ups).

## D7 — Network Bucket Thresholds
**Choice**: HIGH > 60, MEDIUM 21–60, LOW ≤ 20 shared members.
**Rationale**: Defaults from the requirements. Stored in config table for tuning.

## D8 — Geo Distance: Haversine in Python
**Choice**: Haversine formula in Python using numpy vectorized operations. No PostGIS dependency.
**Rationale**: Keeps the stack simple. Zip centroid lookup shipped as a parquet file. Accuracy is sufficient for fraud flagging (not routing).

## D9 — Zip-to-Lat/Lon Lookup
**Choice**: Ship a parquet file with US zip code centroids (~42k rows).
**Rationale**: Small file (~1 MB), no external API dependency, reproducible.

## D10 — Frontend: React + Vite + Tailwind
**Choice**: Vite for fast dev builds, Tailwind for utility-first dark theme, shadcn-style components hand-rolled (no full shadcn install to keep deps minimal).
**Rationale**: Proven stack, fast iteration, easy dark theme via Tailwind.

## D11 — Force Graph: react-force-graph-2d
**Choice**: 2D variant of react-force-graph.
**Rationale**: Simpler, faster rendering for the node counts we expect (hundreds, not millions). 3D can be swapped later.

## D12 — API Prefix: /api/network-graph
**Choice**: All endpoints under `/api/network-graph/`.
**Rationale**: Matches requirement. Allows reverse proxy routing in production.

## D13 — Pagination Default: 100 rows
**Choice**: All list endpoints default to `limit=100, offset=0`.
**Rationale**: Reasonable for dashboard use. Configurable via query params.

## D14 — Audit Logging
**Choice**: Every detection run inserts into `audit_detection_runs` with rule metadata and counts.
**Rationale**: Required for compliance and tuning analysis.

## D15 — PHI Handling
**Choice**: PHI fields (`member_id`, `member_name`, `dob`, `address`) marked with `# PHI` comments in code. Excluded from API response logs via middleware.
**Rationale**: Defense-in-depth. Real PHI protection requires encryption at rest and RBAC, which is out of scope for v1 synthetic mode.

## D16 — Synthetic Data Scale
**Choice**: 10,000 members, 500 prescribers, 200 pharmacies, ~6 months of claims, ~5% planted fraud.
**Rationale**: Matches requirements. Large enough to surface network patterns, small enough for fast local seeding.

## D17 — Docker Compose for Demo
**Choice**: Three services: `db` (postgres:15), `api` (Python), `web` (Node/Vite).
**Rationale**: Single `docker compose up` or `make demo` brings up the full stack.

## D18 — SQL Stored Procedures
**Choice**: Provide equivalent SQL for warehouse-side execution in `backend/sql/procs/`. These mirror the Python detectors but run inside the database.
**Rationale**: Enables scheduling via dbt/Airflow in production without Python runtime.
