.PHONY: install seed generate detect api web demo smoke clean

# --- Config ---
DB_URL ?= postgresql://postgres:postgres@localhost:5432/network_graph
PYTHON ?= python
NPM ?= npm

# --- Install ---
install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt && pip install -e ".[dev]"

install-frontend:
	cd frontend && $(NPM) install

# --- Data ---
generate:
	cd backend && $(PYTHON) -m network_graph_core.synthetic --output-dir ../data/synthetic

seed: generate
	cd backend && DATABASE_URL=$(DB_URL) $(PYTHON) load_data.py --db-url $(DB_URL)

detect:
	cd backend && DATABASE_URL=$(DB_URL) $(PYTHON) run_detections.py --db-url $(DB_URL)

# --- Run ---
api:
	cd backend && DATABASE_URL=$(DB_URL) $(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

web:
	cd frontend && $(NPM) run dev

# --- Full demo ---
demo:
	@echo "=== Network Graph Demo ==="
	@echo "1. Starting database (docker compose up -d db)"
	docker compose up -d db
	@echo "2. Waiting for Postgres..."
	@sleep 3
	@echo "3. Generating synthetic data & seeding..."
	$(MAKE) seed DB_URL=$(DB_URL)
	@echo "4. Running detections..."
	$(MAKE) detect DB_URL=$(DB_URL)
	@echo "5. Starting API server (background)..."
	cd backend && DATABASE_URL=$(DB_URL) $(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
	@sleep 2
	@echo "6. Starting frontend dev server..."
	cd frontend && $(NPM) run dev &
	@sleep 2
	@echo ""
	@echo "=== Demo Ready ==="
	@echo "Frontend: http://localhost:3000"
	@echo "API:      http://localhost:8000/api/network-graph/healthz"
	@echo "API Docs: http://localhost:8000/docs"

# --- Smoke test ---
smoke:
	cd backend && $(PYTHON) ../scripts/smoke_test.py --base-url http://localhost:8000/api/network-graph

# --- Lint ---
lint-backend:
	cd backend && ruff check . && mypy network_graph_core/ api/ --ignore-missing-imports

lint-frontend:
	cd frontend && $(NPM) run lint

lint: lint-backend lint-frontend

# --- Test ---
test:
	cd backend && $(PYTHON) -m pytest tests/ -v --cov=network_graph_core --cov-report=term-missing

# --- Docker ---
docker-up:
	docker compose up --build

docker-down:
	docker compose down -v

# --- Clean ---
clean:
	rm -rf data/synthetic/*.csv
	rm -rf frontend/node_modules frontend/dist
	rm -rf backend/__pycache__ backend/**/__pycache__
