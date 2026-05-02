"""R1 — Suspicious Pharmacy Fills Detector.

Flags pharmacy claims for controlled/abused drugs where the member has
no medical or dental visit within the configured lookback window.
"""

from __future__ import annotations

import pandas as pd

from network_graph_core.config import DetectionConfig


def detect_suspicious_fills(
    pharmacy_claims: pd.DataFrame,
    medical_claims: pd.DataFrame,
    dental_claims: pd.DataFrame,
    drugs: pd.DataFrame,
    config: DetectionConfig,
) -> pd.DataFrame:
    """Detect pharmacy fills without a supporting physician/dental visit.

    Args:
        pharmacy_claims: FACT_PHARMACY_CLAIM with columns
            [claim_id, member_id, prescriber_id, pharmacy_id, drug_id, fill_date, paid_amount]
        medical_claims: FACT_MEDICAL_CLAIM with [claim_id, member_id, service_date]
        dental_claims: FACT_DENTAL_CLAIM with [claim_id, member_id, service_date]
        drugs: DIM_DRUG with [drug_id, drug_class, is_controlled, is_commonly_abused]
        config: DetectionConfig with lookback settings

    Returns:
        DataFrame with columns:
            [claim_id, member_id, prescriber_id, pharmacy_id, drug_id,
             fill_date, paid_amount, rule_name, risk_bucket,
             days_since_last_visit, detection_details]
    """
    # Filter to controlled/abused drugs
    target_drugs = drugs[drugs["is_controlled"] | drugs["is_commonly_abused"]]["drug_id"]
    rx = pharmacy_claims[pharmacy_claims["drug_id"].isin(target_drugs)].copy()

    if rx.empty:
        return _empty_result()

    # Ensure date types
    rx["fill_date"] = pd.to_datetime(rx["fill_date"])

    # Combine medical + dental visits
    visits = pd.concat([
        medical_claims[["member_id", "service_date"]].rename(columns={"service_date": "visit_date"}),
        dental_claims[["member_id", "service_date"]].rename(columns={"service_date": "visit_date"}),
    ], ignore_index=True)
    visits["visit_date"] = pd.to_datetime(visits["visit_date"])

    # Merge drug class for per-class lookback
    rx = rx.merge(drugs[["drug_id", "drug_class"]], on="drug_id", how="left")

    results: list[dict] = []

    for _, fill in rx.iterrows():
        member_id = fill["member_id"]
        fill_date = fill["fill_date"]
        drug_class = fill.get("drug_class", "")
        lookback = config.get_lookback_days(drug_class)

        # Find most recent visit before fill
        member_visits = visits[
            (visits["member_id"] == member_id)
            & (visits["visit_date"] <= fill_date)
            & (visits["visit_date"] >= fill_date - pd.Timedelta(days=lookback))
        ]

        if member_visits.empty:
            # No supporting visit found — flag it
            # Find the most recent visit ever for days_since calculation
            all_member_visits = visits[
                (visits["member_id"] == member_id) & (visits["visit_date"] <= fill_date)
            ]
            if all_member_visits.empty:
                days_since = -1  # No visit on record
            else:
                last_visit = all_member_visits["visit_date"].max()
                days_since = (fill_date - last_visit).days

            results.append({
                "claim_id": fill["claim_id"],
                "member_id": member_id,
                "prescriber_id": fill["prescriber_id"],
                "pharmacy_id": fill["pharmacy_id"],
                "drug_id": fill["drug_id"],
                "fill_date": fill_date,
                "paid_amount": fill["paid_amount"],
                "rule_name": "suspicious_fills",
                "risk_bucket": _bucket(days_since, lookback),
                "days_since_last_visit": days_since,
                "detection_details": (
                    f"No medical/dental visit within {lookback}-day lookback. "
                    f"Days since last visit: {days_since}. Drug class: {drug_class}"
                ),
            })

    if not results:
        return _empty_result()

    return pd.DataFrame(results)


def _bucket(days_since: int, lookback: int) -> str:
    """Assign risk bucket based on gap severity."""
    if days_since == -1:
        return "HIGH"  # No visit ever
    if days_since > lookback * 2:
        return "HIGH"
    if days_since > lookback:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "claim_id", "member_id", "prescriber_id", "pharmacy_id", "drug_id",
        "fill_date", "paid_amount", "rule_name", "risk_bucket",
        "days_since_last_visit", "detection_details",
    ])
