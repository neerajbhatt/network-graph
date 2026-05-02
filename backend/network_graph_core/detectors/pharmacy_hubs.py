"""R4.3 — Pharmacy-Centric Hub Detection.

Flags pharmacies receiving controlled-drug prescriptions from >= N distinct
prescribers for the same member cohort.
"""

from __future__ import annotations

import pandas as pd

from network_graph_core.config import DetectionConfig


def detect_pharmacy_hubs(
    pharmacy_claims: pd.DataFrame,
    drugs: pd.DataFrame,
    config: DetectionConfig,
) -> pd.DataFrame:
    """Detect pharmacies acting as hubs for controlled substances.

    Args:
        pharmacy_claims: FACT_PHARMACY_CLAIM
        drugs: DIM_DRUG
        config: DetectionConfig with pharmacy_hub_min_prescribers

    Returns:
        DataFrame with columns:
            [pharmacy_id, distinct_prescriber_count, distinct_member_count,
             total_claims, total_exposure, risk_bucket, prescriber_ids]
    """
    target_drugs = drugs[drugs["is_controlled"] | drugs["is_commonly_abused"]]["drug_id"]
    rx = pharmacy_claims[pharmacy_claims["drug_id"].isin(target_drugs)].copy()

    if rx.empty:
        return _empty_result()

    agg = (
        rx.groupby("pharmacy_id")
        .agg(
            distinct_prescriber_count=("prescriber_id", "nunique"),
            distinct_member_count=("member_id", "nunique"),
            total_claims=("claim_id", "count"),
            total_exposure=("paid_amount", "sum"),
            prescriber_ids=("prescriber_id", lambda x: list(x.unique())),
        )
        .reset_index()
    )

    min_prescribers = config.pharmacy_hub_min_prescribers
    flagged = agg[agg["distinct_prescriber_count"] >= min_prescribers].copy()

    if flagged.empty:
        return _empty_result()

    flagged["risk_bucket"] = flagged["distinct_prescriber_count"].apply(_bucket)
    flagged["total_exposure"] = flagged["total_exposure"].round(2)

    return flagged.sort_values("distinct_prescriber_count", ascending=False).reset_index(drop=True)


def _bucket(count: int) -> str:
    if count >= 20:
        return "HIGH"
    if count >= 10:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "pharmacy_id", "distinct_prescriber_count", "distinct_member_count",
        "total_claims", "total_exposure", "risk_bucket", "prescriber_ids",
    ])
