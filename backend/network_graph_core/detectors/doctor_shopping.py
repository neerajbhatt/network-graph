"""R4.2 — Member Doctor-Shopping Detection.

Flags members filling controlled drugs at >= N pharmacies or
seeing >= N prescribers within the lookback window.
"""

from __future__ import annotations

import pandas as pd

from network_graph_core.config import DetectionConfig


def detect_doctor_shoppers(
    pharmacy_claims: pd.DataFrame,
    drugs: pd.DataFrame,
    config: DetectionConfig,
) -> pd.DataFrame:
    """Detect members exhibiting doctor-shopping behavior.

    Args:
        pharmacy_claims: FACT_PHARMACY_CLAIM with
            [claim_id, member_id, prescriber_id, pharmacy_id, drug_id,
             fill_date, paid_amount]
        drugs: DIM_DRUG with [drug_id, is_controlled, is_commonly_abused]
        config: DetectionConfig with doctor_shopping_min_pharmacies,
                doctor_shopping_min_prescribers

    Returns:
        DataFrame with columns:
            [member_id, pharmacy_count, prescriber_count,
             controlled_fill_count, total_exposure, risk_bucket,
             first_fill_date, last_fill_date, pharmacy_ids, prescriber_ids]
    """
    target_drugs = drugs[drugs["is_controlled"] | drugs["is_commonly_abused"]]["drug_id"]
    rx = pharmacy_claims[pharmacy_claims["drug_id"].isin(target_drugs)].copy()

    if rx.empty:
        return _empty_result()

    rx["fill_date"] = pd.to_datetime(rx["fill_date"])

    agg = (
        rx.groupby("member_id")
        .agg(
            pharmacy_count=("pharmacy_id", "nunique"),
            prescriber_count=("prescriber_id", "nunique"),
            controlled_fill_count=("claim_id", "count"),
            total_exposure=("paid_amount", "sum"),
            first_fill_date=("fill_date", "min"),
            last_fill_date=("fill_date", "max"),
            pharmacy_ids=("pharmacy_id", lambda x: list(x.unique())),
            prescriber_ids=("prescriber_id", lambda x: list(x.unique())),
        )
        .reset_index()
    )

    # Filter: must exceed at least one threshold
    min_pharm = config.doctor_shopping_min_pharmacies
    min_presc = config.doctor_shopping_min_prescribers
    flagged = agg[
        (agg["pharmacy_count"] >= min_pharm)
        | (agg["prescriber_count"] >= min_presc)
    ].copy()

    if flagged.empty:
        return _empty_result()

    flagged["risk_bucket"] = flagged.apply(
        lambda r: _bucket(r["pharmacy_count"], r["prescriber_count"]),
        axis=1,
    )
    flagged["total_exposure"] = flagged["total_exposure"].round(2)

    return flagged.sort_values("total_exposure", ascending=False).reset_index(drop=True)


def _bucket(pharmacy_count: int, prescriber_count: int) -> str:
    if pharmacy_count >= 5 or prescriber_count >= 5:
        return "HIGH"
    if pharmacy_count >= 3 or prescriber_count >= 3:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "member_id", "pharmacy_count", "prescriber_count",
        "controlled_fill_count", "total_exposure", "risk_bucket",
        "first_fill_date", "last_fill_date", "pharmacy_ids", "prescriber_ids",
    ])
