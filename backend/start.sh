#!/usr/bin/env bash
set -e

export DATA_DIR="/app/data/synthetic"

echo "=== Generating synthetic data ==="
python -m network_graph_core.synthetic --output-dir "$DATA_DIR"

echo "=== Loading data into database ==="
python load_data.py --data-dir "$DATA_DIR"

echo "=== Running detections ==="
python run_detections.py

echo "=== Starting API server ==="
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
