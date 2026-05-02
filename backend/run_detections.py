"""Run all detection algorithms and persist results.

Usage:
    python backend/run_detections.py [--db-url postgresql://...]
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime

import pandas as pd
import sqlalchemy
from sqlalchemy import text

from network_graph_core.config import DetectionConfig
from network_graph_core.detectors.geo_anomaly import detect_geo_anomalies
from network_graph_core.detectors.suspicious_fills import detect_suspicious_fills

DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/network_graph",
)


def run_all(db_url: str) -> None:
    engine = sqlalchemy.create_engine(db_url)

    # Load config
    with engine.connect() as conn:
        rules = pd.read_sql("SELECT * FROM network_graph.config_detection_rules", conn)
    config = DetectionConfig.from_rules(rules.to_dict("records"))

    # Load data
    with engine.connect() as conn:
        pharmacy_claims = pd.read_sql("SELECT * FROM network_graph.fact_pharmacy_claim", conn)
        medical_claims = pd.read_sql("SELECT * FROM network_graph.fact_medical_claim", conn)
        dental_claims = pd.read_sql("SELECT * FROM network_graph.fact_dental_claim", conn)
        drugs = pd.read_sql("SELECT * FROM network_graph.dim_drug", conn)
        members = pd.read_sql("SELECT * FROM network_graph.dim_member", conn)
        pharmacies = pd.read_sql("SELECT * FROM network_graph.dim_pharmacy", conn)

    print(
        f"Loaded {len(pharmacy_claims):,} pharmacy claims, "
        f"{len(medical_claims):,} medical, {len(dental_claims):,} dental"
    )

    # Clear previous results
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE network_graph.fact_suspicious_fill"))
        conn.commit()

    # --- R1: Suspicious Fills ---
    print("Running: Suspicious Fills...")
    sf_result = detect_suspicious_fills(pharmacy_claims, medical_claims, dental_claims, drugs, config)
    _persist_results(engine, sf_result, "suspicious_fills", len(pharmacy_claims))
    print(f"  Flagged: {len(sf_result):,}")

    # --- R6: Geo Anomalies ---
    print("Running: Geo Anomalies...")
    geo_result = detect_geo_anomalies(pharmacy_claims, members, pharmacies, drugs, config)
    _persist_results(engine, geo_result, "geo_anomaly", len(pharmacy_claims))
    print(f"  Flagged: {len(geo_result):,}")

    print("\nDetection runs complete.")


def _persist_results(
    engine: sqlalchemy.engine.Engine,
    results: pd.DataFrame,
    rule_name: str,
    input_count: int,
) -> None:
    """Write detection results to fact_suspicious_fill and audit log."""
    if results.empty:
        _audit(engine, rule_name, input_count, 0)
        return

    # Write audit log first to get run_id
    run_id = _audit(engine, rule_name, input_count, len(results))

    # Prepare for insert
    insert_df = results.copy()
    insert_df["audit_run_id"] = run_id
    insert_df["detected_at"] = datetime.utcnow()

    # Only keep columns that exist in the table
    table_cols = [
        "claim_id", "member_id", "prescriber_id", "pharmacy_id", "drug_id",
        "fill_date", "paid_amount", "rule_name", "risk_bucket",
        "days_since_last_visit", "distance_miles", "detection_details",
        "detected_at", "audit_run_id",
    ]
    for col in table_cols:
        if col not in insert_df.columns:
            insert_df[col] = None

    insert_df = insert_df[[c for c in table_cols if c in insert_df.columns]]

    insert_df.to_sql(
        "fact_suspicious_fill",
        engine,
        schema="network_graph",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )


def _audit(
    engine: sqlalchemy.engine.Engine,
    rule_name: str,
    input_count: int,
    flagged_count: int,
) -> int:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                INSERT INTO network_graph.audit_detection_runs
                    (rule_name, rule_version, input_count, flagged_count, status)
                VALUES (:rule_name, '1.0', :input_count, :flagged_count, 'COMPLETED')
                RETURNING run_id
            """),
            {"rule_name": rule_name, "input_count": input_count, "flagged_count": flagged_count},
        )
        run_id = result.scalar()
        conn.commit()
    return int(run_id)  # type: ignore[arg-type]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Network Graph detections")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL)
    args = parser.parse_args()
    run_all(args.db_url)


if __name__ == "__main__":
    main()
