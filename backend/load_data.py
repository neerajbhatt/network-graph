"""Load synthetic CSV data into PostgreSQL.

Usage:
    python backend/load_data.py [--data-dir data/synthetic] [--db-url postgresql://...]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import sqlalchemy
from sqlalchemy import text

DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/network_graph",
)

DATA_DIR = Path("data/synthetic")

# Load order matters for FK constraints
TABLES = [
    ("dim_member", "network_graph.dim_member"),
    ("dim_prescriber", "network_graph.dim_prescriber"),
    ("dim_pharmacy", "network_graph.dim_pharmacy"),
    ("dim_drug", "network_graph.dim_drug"),
    ("fact_pharmacy_claim", "network_graph.fact_pharmacy_claim"),
    ("fact_medical_claim", "network_graph.fact_medical_claim"),
    ("fact_dental_claim", "network_graph.fact_dental_claim"),
]


def load_data(data_dir: Path, db_url: str) -> None:
    engine = sqlalchemy.create_engine(db_url)

    # Run DDL
    ddl_dir = Path("backend/sql/ddl")
    ddl_files = sorted(ddl_dir.glob("*.sql"))
    with engine.connect() as conn:
        for ddl_file in ddl_files:
            print(f"Running DDL: {ddl_file.name}")
            sql = ddl_file.read_text()
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
        conn.commit()

    # Run seed SQL
    seed_dir = Path("backend/sql/seed")
    seed_files = sorted(seed_dir.glob("*.sql"))
    with engine.connect() as conn:
        for seed_file in seed_files:
            print(f"Running seed: {seed_file.name}")
            sql = seed_file.read_text()
            conn.execute(text(sql))
        conn.commit()

    # Load CSVs
    for csv_name, table_name in TABLES:
        csv_path = data_dir / f"{csv_name}.csv"
        if not csv_path.exists():
            print(f"  SKIP {csv_name} — CSV not found at {csv_path}")
            continue

        df = pd.read_csv(csv_path)

        # Truncate existing data
        schema, tbl = table_name.split(".")
        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            conn.commit()

        # Insert
        df.to_sql(
            tbl,
            engine,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
        print(f"  Loaded {csv_name}: {len(df):,} rows")

    print("\nData load complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load synthetic data into Postgres")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--db-url", default=DEFAULT_DB_URL)
    args = parser.parse_args()
    load_data(args.data_dir, args.db_url)


if __name__ == "__main__":
    main()
