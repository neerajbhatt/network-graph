"""Tests for R4.3 — Pharmacy Hub Detection."""

from __future__ import annotations

import pandas as pd

from network_graph_core.config import DetectionConfig
from network_graph_core.detectors.pharmacy_hubs import detect_pharmacy_hubs


class TestPharmacyHubs:
    def test_hub_detected(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Pharmacy with 10 prescribers => MEDIUM hub."""
        rows = [
            {"claim_id": i, "member_id": 1, "prescriber_id": i,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 100.0}
            for i in range(1, 11)
        ]
        rx = pd.DataFrame(rows)
        result = detect_pharmacy_hubs(rx, drugs, config)
        assert len(result) == 1
        assert result.iloc[0]["distinct_prescriber_count"] == 10
        assert result.iloc[0]["risk_bucket"] == "MEDIUM"

    def test_high_hub(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Pharmacy with 25 prescribers => HIGH hub."""
        rows = [
            {"claim_id": i, "member_id": 1, "prescriber_id": i,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 100.0}
            for i in range(1, 26)
        ]
        rx = pd.DataFrame(rows)
        result = detect_pharmacy_hubs(rx, drugs, config)
        assert result.iloc[0]["risk_bucket"] == "HIGH"

    def test_below_threshold_not_flagged(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Pharmacy with < min_prescribers should not be flagged."""
        rows = [
            {"claim_id": i, "member_id": 1, "prescriber_id": i,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 100.0}
            for i in range(1, 4)
        ]
        rx = pd.DataFrame(rows)
        result = detect_pharmacy_hubs(rx, drugs, config)
        assert len(result) == 0

    def test_planted_hubs_recall(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Plant 5 hub pharmacies — recall must be >= 0.9."""
        rows = []
        cid = 1
        for pharm_id in range(1, 6):
            for presc_id in range(1, 11):  # 10 prescribers each
                rows.append({
                    "claim_id": cid, "member_id": presc_id,
                    "prescriber_id": presc_id, "pharmacy_id": pharm_id,
                    "drug_id": 1, "paid_amount": 100.0,
                })
                cid += 1
        rx = pd.DataFrame(rows)
        result = detect_pharmacy_hubs(rx, drugs, config)
        recall = len(result) / 5
        assert recall >= 0.9, f"Recall {recall} < 0.9"
