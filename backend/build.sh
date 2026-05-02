#!/usr/bin/env bash
set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt
pip install -e .

echo "=== Generating synthetic data ==="
python -m network_graph_core.synthetic --output-dir ../data/synthetic

echo "=== Loading data into database ==="
python load_data.py

echo "=== Running detections ==="
python run_detections.py

echo "=== Build complete ==="
