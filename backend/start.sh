#!/usr/bin/env bash
set -e

export DATA_DIR="/app/data/synthetic"

# Check if data already exists in DB; skip heavy pipeline if so
DATA_EXISTS=$(python -c "
import os, sqlalchemy
url = os.environ.get('DATABASE_URL','')
if not url:
    print('no')
    exit()
try:
    engine = sqlalchemy.create_engine(url)
    with engine.connect() as conn:
        r = conn.execute(sqlalchemy.text('SELECT COUNT(*) FROM network_graph.fact_pharmacy_claim'))
        cnt = r.scalar()
        print('yes' if cnt and cnt > 0 else 'no')
except Exception:
    print('no')
" 2>/dev/null || echo "no")

if [ "$DATA_EXISTS" = "yes" ]; then
    echo "=== Data already loaded (skipping generation/load/detection) ==="
else
    echo "=== Generating synthetic data ==="
    python -m network_graph_core.synthetic --output-dir "$DATA_DIR"

    echo "=== Loading data into database ==="
    python load_data.py --data-dir "$DATA_DIR"

    echo "=== Running detections ==="
    python run_detections.py
fi

# Background keep-alive: ping frontend every 13 min to prevent Render sleep
(
    sleep 120
    while true; do
        curl -sf --max-time 30 "https://network-graph-web.onrender.com/" > /dev/null 2>&1 || true
        sleep 780
    done
) &

echo "=== Starting API server ==="
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
