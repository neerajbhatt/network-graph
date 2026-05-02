"""R6 — Geo-Distance Anomaly Detection.

Flags pharmacy fills where the Haversine distance between member home zip
centroid and pharmacy zip centroid exceeds:
  - 95th percentile of the member's history, OR
  - absolute threshold (default 50 miles)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from network_graph_core.config import DetectionConfig


def haversine_miles(
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: np.ndarray,
    lon2: np.ndarray,
) -> np.ndarray:
    """Vectorized Haversine distance in miles."""
    earth_radius = 3958.8  # Earth radius in miles
    lat1_r, lat2_r = np.radians(lat1), np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
    return 2 * earth_radius * np.arcsin(np.sqrt(a))


def detect_geo_anomalies(
    pharmacy_claims: pd.DataFrame,
    members: pd.DataFrame,
    pharmacies: pd.DataFrame,
    drugs: pd.DataFrame,
    config: DetectionConfig,
) -> pd.DataFrame:
    """Detect fills with anomalous member-to-pharmacy distances.

    Args:
        pharmacy_claims: FACT_PHARMACY_CLAIM with
            [claim_id, member_id, pharmacy_id, drug_id, fill_date, paid_amount]
        members: DIM_MEMBER with [member_id, latitude, longitude]
        pharmacies: DIM_PHARMACY with [pharmacy_id, latitude, longitude]
        drugs: DIM_DRUG with [drug_id, is_controlled, is_commonly_abused]
        config: DetectionConfig with geo thresholds

    Returns:
        DataFrame with columns:
            [claim_id, member_id, prescriber_id, pharmacy_id, drug_id,
             fill_date, paid_amount, distance_miles, rule_name, risk_bucket,
             detection_details]
    """
    target_drugs = drugs[drugs["is_controlled"] | drugs["is_commonly_abused"]]["drug_id"]
    rx = pharmacy_claims[pharmacy_claims["drug_id"].isin(target_drugs)].copy()

    if rx.empty:
        return _empty_result()

    # Join member and pharmacy coordinates
    rx = rx.merge(
        members[["member_id", "latitude", "longitude"]].rename(
            columns={"latitude": "member_lat", "longitude": "member_lon"}
        ),
        on="member_id",
        how="left",
    )
    rx = rx.merge(
        pharmacies[["pharmacy_id", "latitude", "longitude"]].rename(
            columns={"latitude": "pharm_lat", "longitude": "pharm_lon"}
        ),
        on="pharmacy_id",
        how="left",
    )

    # Drop rows with missing coordinates
    rx = rx.dropna(subset=["member_lat", "member_lon", "pharm_lat", "pharm_lon"])

    if rx.empty:
        return _empty_result()

    # Compute distances
    rx["distance_miles"] = haversine_miles(
        rx["member_lat"].values,
        rx["member_lon"].values,
        rx["pharm_lat"].values,
        rx["pharm_lon"].values,
    )

    abs_threshold = config.geo_distance_absolute_miles
    pct_threshold = config.geo_distance_percentile

    # Compute per-member percentile thresholds
    member_pcts = (
        rx.groupby("member_id")["distance_miles"]
        .quantile(pct_threshold / 100.0)
        .rename("member_pct_threshold")
        .reset_index()
    )
    rx = rx.merge(member_pcts, on="member_id", how="left")

    # Flag: exceeds absolute threshold OR member's percentile threshold
    flagged = rx[
        (rx["distance_miles"] > abs_threshold)
        | (rx["distance_miles"] > rx["member_pct_threshold"])
    ].copy()

    if flagged.empty:
        return _empty_result()

    flagged["rule_name"] = "geo_anomaly"
    flagged["risk_bucket"] = flagged["distance_miles"].apply(
        lambda d: _bucket(d, abs_threshold)
    )
    flagged["detection_details"] = flagged.apply(
        lambda r: (
            f"Distance: {r['distance_miles']:.1f} miles. "
            f"Absolute threshold: {abs_threshold} miles. "
            f"Member 95th pct: {r['member_pct_threshold']:.1f} miles"
        ),
        axis=1,
    )
    flagged["distance_miles"] = flagged["distance_miles"].round(2)

    result_cols = [
        "claim_id", "member_id", "prescriber_id", "pharmacy_id", "drug_id",
        "fill_date", "paid_amount", "distance_miles", "rule_name", "risk_bucket",
        "detection_details",
    ]
    return flagged[result_cols].reset_index(drop=True)


def _bucket(distance: float, threshold: float) -> str:
    if distance > threshold * 3:
        return "HIGH"
    if distance > threshold:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "claim_id", "member_id", "prescriber_id", "pharmacy_id", "drug_id",
        "fill_date", "paid_amount", "distance_miles", "rule_name", "risk_bucket",
        "detection_details",
    ])
