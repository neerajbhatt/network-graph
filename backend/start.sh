#!/usr/bin/env bash
set -e

echo "=== Generating synthetic data ==="
python -m network_graph_core.synthetic --output-dir /app/data/synthetic

echo "=== Loading data into database ==="
python load_data.py

echo "=== Running detections ==="
python run_detections.py

echo "=== Starting API server ==="
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
