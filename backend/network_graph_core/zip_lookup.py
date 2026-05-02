"""Zip code to lat/lon centroid lookup.

Ships a generated parquet file with ~1000 representative US zip codes for the synthetic data.
For production, replace with the full USPS zip centroid file.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PARQUET_PATH = DATA_DIR / "zip_centroids.parquet"

# Cache
_zip_lookup: pd.DataFrame | None = None


def generate_zip_centroids(n: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Generate representative zip centroids across US states."""
    rng = np.random.default_rng(seed)

    states_bounds = [
        ("TX", 26.0, 36.5, -106.6, -93.5),
        ("CA", 32.5, 42.0, -124.4, -114.1),
        ("FL", 24.5, 31.0, -87.6, -80.0),
        ("NY", 40.5, 45.0, -79.8, -71.8),
        ("PA", 39.7, 42.3, -80.5, -74.7),
        ("IL", 37.0, 42.5, -91.5, -87.5),
        ("OH", 38.4, 42.0, -84.8, -80.5),
        ("GA", 30.4, 35.0, -85.6, -80.8),
        ("NC", 33.8, 36.6, -84.3, -75.5),
        ("MI", 41.7, 48.3, -90.4, -82.1),
    ]

    rows = []
    per_state = n // len(states_bounds)
    for state, lat_min, lat_max, lon_min, lon_max in states_bounds:
        for _ in range(per_state):
            rows.append({
                "zip": f"{rng.integers(10000, 99999):05d}",
                "latitude": round(float(rng.uniform(lat_min, lat_max)), 6),
                "longitude": round(float(rng.uniform(lon_min, lon_max)), 6),
                "state": state,
            })

    df = pd.DataFrame(rows).drop_duplicates(subset=["zip"])
    return df


def get_zip_centroids() -> pd.DataFrame:
    """Load or generate zip centroid lookup."""
    global _zip_lookup
    if _zip_lookup is not None:
        return _zip_lookup

    if PARQUET_PATH.exists():
        _zip_lookup = pd.read_parquet(PARQUET_PATH)
    else:
        _zip_lookup = generate_zip_centroids()
        PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
        _zip_lookup.to_parquet(PARQUET_PATH, index=False)

    return _zip_lookup
