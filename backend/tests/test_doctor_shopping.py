"""Tests for R4.2 — Doctor Shopping Detection."""

from __future__ import annotations

from datetime import date

import pandas as pd

from network_graph_core.config import DetectionConfig
from network_graph_core.detectors.doctor_shopping import detect_doctor_shoppers


class TestDoctorShopping:
    def test_shopper_detected(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Member visiting 5 pharmacies and 5 prescribers should be HIGH."""
        rows = []
        for i in range(1, 11):
            rows.append({
                "claim_id": i, "member_id": 1,
                "prescriber_id": (i % 5) + 1,
                "pharmacy_id": (i % 5) + 1,
                "drug_id": 1, "fill_date": date(2025, 10, i),
                "paid_amount": 100.0,
            })
        rx = pd.DataFrame(rows)
        result = detect_doctor_shoppers(rx, drugs, config)
        assert len(result) == 1
        assert result.iloc[0]["risk_bucket"] == "HIGH"

    def test_normal_member_not_flagged(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Member using 1 pharmacy and 1 prescriber should not be flagged."""
        rows = [{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 1, "fill_date": date(2025, 10, 1),
            "paid_amount": 50.0,
        }]
        rx = pd.DataFrame(rows)
        result = detect_doctor_shoppers(rx, drugs, config)
        assert len(result) == 0

    def test_planted_shoppers_recall(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Plant 10 doctor shoppers — recall must be >= 0.9."""
        rows = []
        cid = 1
        for member_id in range(1, 11):
            for pharm_id in range(1, 6):  # 5 pharmacies each
                for presc_id in range(1, 6):
                    rows.append({
                        "claim_id": cid, "member_id": member_id,
                        "prescriber_id": presc_id, "pharmacy_id": pharm_id,
                        "drug_id": 1, "fill_date": date(2025, 10, 1),
                        "paid_amount": 100.0,
                    })
                    cid += 1
        rx = pd.DataFrame(rows)
        result = detect_doctor_shoppers(rx, drugs, config)
        recall = len(result) / 10
        assert recall >= 0.9, f"Recall {recall} < 0.9"

    def test_medium_bucket(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Member with 3 pharmacies should be MEDIUM."""
        rows = []
        for i in range(1, 4):
            rows.append({
                "claim_id": i, "member_id": 1, "prescriber_id": 1,
                "pharmacy_id": i, "drug_id": 1, "fill_date": date(2025, 10, i),
                "paid_amount": 100.0,
            })
        rx = pd.DataFrame(rows)
        result = detect_doctor_shoppers(rx, drugs, config)
        assert len(result) == 1
        assert result.iloc[0]["risk_bucket"] == "MEDIUM"
