"""R2 — Prescriber-Pharmacy Network Detection.

Builds a graph of prescribers and pharmacies linked by shared members.
Buckets edges by shared-member count: HIGH / MEDIUM / LOW.
"""

from __future__ import annotations

import pandas as pd

from network_graph_core.config import DetectionConfig


def detect_network_buckets(
    pharmacy_claims: pd.DataFrame,
    drugs: pd.DataFrame,
    config: DetectionConfig,
) -> pd.DataFrame:
    """Detect prescriber-pharmacy network edges and bucket by shared members.

    Args:
        pharmacy_claims: FACT_PHARMACY_CLAIM with
            [claim_id, member_id, prescriber_id, pharmacy_id, drug_id, paid_amount]
        drugs: DIM_DRUG with [drug_id, is_controlled, is_commonly_abused]
        config: DetectionConfig with high_threshold, medium_threshold

    Returns:
        DataFrame with columns:
            [prescriber_id, pharmacy_id, shared_member_count, risk_bucket,
             total_exposure, member_ids]
    """
    # Filter to controlled/abused drugs
    target_drugs = drugs[drugs["is_controlled"] | drugs["is_commonly_abused"]]["drug_id"]
    rx = pharmacy_claims[pharmacy_claims["drug_id"].isin(target_drugs)].copy()

    if rx.empty:
        return _empty_result()

    # Group by prescriber-pharmacy pair, count distinct members
    edges = (
        rx.groupby(["prescriber_id", "pharmacy_id"])
        .agg(
            shared_member_count=("member_id", "nunique"),
            total_exposure=("paid_amount", "sum"),
            member_ids=("member_id", lambda x: list(x.unique())),
        )
        .reset_index()
    )

    # Assign buckets
    edges["risk_bucket"] = edges["shared_member_count"].apply(
        lambda c: _bucket(c, config.high_threshold, config.medium_threshold)
    )

    edges["total_exposure"] = edges["total_exposure"].round(2)

    return edges.sort_values("shared_member_count", ascending=False).reset_index(drop=True)


def _bucket(count: int, high: int, medium: int) -> str:
    if count > high:
        return "HIGH"
    if count > medium:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "prescriber_id", "pharmacy_id", "shared_member_count",
        "risk_bucket", "total_exposure", "member_ids",
    ])
