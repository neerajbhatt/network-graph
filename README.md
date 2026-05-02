# Network Graph

**Pharmacy Fraud & Abuse Detection Platform**

Detect potential fraud, abuse, or misuse in pharmacy claims for controlled and commonly-abused drugs. Surface suspicious networks including doctor shopping, prescriber-pharmacy collusion, pharmacy hubs, and geographic anomalies.

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)
- Git Bash (Windows) or Bash (macOS/Linux)

### Option 1: Docker (recommended)

```bash
# Clone and start everything
git clone <repo-url> network-graph && cd network-graph
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000/api/network-graph/healthz
- API Docs: http://localhost:8000/docs

### Option 2: Local development

```bash
# 1. Start PostgreSQL (via Docker or local install)
docker compose up -d db

# 2. Install dependencies
make install

# 3. Generate synthetic data, load into DB, run detections
make seed
make detect

# 4. Start API (terminal 1)
make api

# 5. Start frontend (terminal 2)
make web
```

### Option 3: One-command demo

```bash
make demo
```

This starts the DB, generates data, runs detections, and launches both servers.

## Architecture

```
Frontend (React/Vite/Tailwind) → FastAPI → PostgreSQL
                                    ↓
                           network_graph_core/
                           (detection engine)
```

See [docs/architecture.md](docs/architecture.md) for the full ERD and system design.

## Project Structure

```
network-graph/
├── backend/
│   ├── network_graph_core/      # Reusable detection package
│   │   ├── detectors/           # 5 detector modules
│   │   ├── synthetic.py         # Synthetic data generator
│   │   └── config.py            # Configuration management
│   ├── api/                     # FastAPI application
│   ├── sql/
│   │   ├── ddl/                 # Table definitions
│   │   ├── seed/                # Reference data seeds
│   │   └── procs/               # SQL stored procedures
│   └── tests/                   # Unit tests
├── frontend/
│   └── src/
│       ├── components/          # Shared UI components
│       ├── pages/               # 5 tab pages
│       └── lib/                 # API client
├── data/synthetic/              # Generated CSV data
├── docs/                        # Architecture, Power BI docs
├── scripts/                     # Smoke test
├── Makefile                     # Build/run commands
└── docker-compose.yml           # Full stack orchestration
```

## API Endpoints

All under `/api/network-graph/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/healthz` | Health check |
| GET | `/kpi` | KPI summary cards |
| GET | `/networks` | Prescriber-pharmacy network graph |
| GET | `/networks/{id}/drill` | Drill into a network node |
| GET | `/doctor-shoppers` | Members with doctor-shopping patterns |
| GET | `/pharmacy-hubs` | Pharmacy hub analysis |
| GET | `/geo-outliers` | Geographic anomaly flags |
| GET | `/config/rules` | Current detection thresholds |
| PUT | `/config/rules` | Update detection thresholds |

## Frontend Tabs

1. **Networks** — Force-directed graph visualization of prescriber-pharmacy networks
2. **Doctor Shoppers** — Sortable table with member detail drawer
3. **Pharmacy Hubs** — Table + bar chart of top hubs
4. **Geo Outliers** — Leaflet map with member-to-pharmacy distance lines
5. **Config** — Edit detection thresholds

## Detection Rules

| Rule | Description | Default Threshold |
|------|-------------|-------------------|
| Suspicious Fills (R1) | No medical/dental visit within lookback | 30-day lookback |
| Network Buckets (R2) | Shared member count between prescriber-pharmacy pairs | HIGH > 60, MEDIUM > 20 |
| Doctor Shopping (R4.2) | Members at multiple pharmacies/prescribers | >= 3 pharmacies or prescribers |
| Pharmacy Hubs (R4.3) | Pharmacies with many distinct prescribers | >= 5 prescribers |
| Geo Anomaly (R6) | Member-to-pharmacy distance outliers | > 50 miles or > 95th percentile |

All thresholds are configurable via the Config tab or `CONFIG_DETECTION_RULES` table.

## Switching to Real Data

1. Set environment variable: `DATA_MODE=REAL`
2. Populate the dimension and fact tables via your ETL pipeline (same DDL schema)
3. Run detections: `make detect`
4. The API and frontend work identically — they read from the same tables

## Power BI Integration

See [docs/powerbi.md](docs/powerbi.md) for:
- RPT_* view documentation
- Sample DAX measures
- Connection setup guide

## Testing

```bash
# Run unit tests with coverage
make test

# Run smoke test (requires running API)
make smoke

# Lint
make lint
```

## Key Decisions

See [DECISIONS.md](DECISIONS.md) for all architectural choices and rationale.

## Open Questions

See [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) for items requiring human review.
