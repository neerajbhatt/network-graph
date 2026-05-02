"""Tests for R1 — Suspicious Fill Detection."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from network_graph_core.config import DetectionConfig
from network_graph_core.detectors.suspicious_fills import detect_suspicious_fills


def _make_pharmacy_claims(fills: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(fills)


def _make_visits(visits: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(visits, columns=["claim_id", "member_id", "service_date"])


class TestSuspiciousFills:
    def test_no_visit_flags_fill(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """A controlled fill with no medical/dental visit should be flagged."""
        rx = _make_pharmacy_claims([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 1, "fill_date": date(2025, 10, 15),
            "paid_amount": 100.0,
        }])
        medical = _make_visits([])
        dental = _make_visits([])

        result = detect_suspicious_fills(rx, medical, dental, drugs, config)
        assert len(result) == 1
        assert result.iloc[0]["claim_id"] == 1
        assert result.iloc[0]["risk_bucket"] == "HIGH"

    def test_recent_visit_no_flag(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """A fill with a medical visit within lookback should NOT be flagged."""
        fill_date = date(2025, 10, 15)
        rx = _make_pharmacy_claims([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 1, "fill_date": fill_date,
            "paid_amount": 100.0,
        }])
        medical = _make_visits([{
            "claim_id": 100, "member_id": 1,
            "service_date": fill_date - timedelta(days=10),
        }])
        dental = _make_visits([])

        result = detect_suspicious_fills(rx, medical, dental, drugs, config)
        assert len(result) == 0

    def test_dental_visit_prevents_flag(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """A dental visit within lookback should prevent flagging."""
        fill_date = date(2025, 10, 15)
        rx = _make_pharmacy_claims([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 1, "fill_date": fill_date,
            "paid_amount": 100.0,
        }])
        medical = _make_visits([])
        dental = _make_visits([{
            "claim_id": 200, "member_id": 1,
            "service_date": fill_date - timedelta(days=5),
        }])

        result = detect_suspicious_fills(rx, medical, dental, drugs, config)
        assert len(result) == 0

    def test_non_controlled_not_flagged(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Non-controlled drugs should not be flagged even without visits."""
        rx = _make_pharmacy_claims([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 3, "fill_date": date(2025, 10, 15),
            "paid_amount": 50.0,
        }])
        medical = _make_visits([])
        dental = _make_visits([])

        result = detect_suspicious_fills(rx, medical, dental, drugs, config)
        assert len(result) == 0

    def test_planted_pattern_recall(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Plant 10 suspicious fills — all should be detected (recall >= 0.9)."""
        fill_date = date(2025, 10, 15)
        rx_rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 1, "drug_id": 1, "fill_date": fill_date,
             "paid_amount": 100.0}
            for i in range(1, 11)
        ]
        rx = _make_pharmacy_claims(rx_rows)
        medical = _make_visits([])
        dental = _make_visits([])

        result = detect_suspicious_fills(rx, medical, dental, drugs, config)
        recall = len(result) / 10
        assert recall >= 0.9, f"Recall {recall} < 0.9"

    def test_old_visit_beyond_lookback(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """A visit outside the lookback window should still result in a flag."""
        fill_date = date(2025, 10, 15)
        rx = _make_pharmacy_claims([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 1, "fill_date": fill_date,
            "paid_amount": 100.0,
        }])
        medical = _make_visits([{
            "claim_id": 100, "member_id": 1,
            "service_date": fill_date - timedelta(days=60),
        }])
        dental = _make_visits([])

        result = detect_suspicious_fills(rx, medical, dental, drugs, config)
        assert len(result) == 1
        assert result.iloc[0]["days_since_last_visit"] == 60
