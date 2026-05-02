"""Tests for R2 — Network Bucket Detection."""

from __future__ import annotations

import pandas as pd

from network_graph_core.config import DetectionConfig
from network_graph_core.detectors.network_buckets import detect_network_buckets


class TestNetworkBuckets:
    def test_high_bucket(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """A prescriber-pharmacy pair with >60 shared members => HIGH."""
        rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 100.0}
            for i in range(1, 70)
        ]
        rx = pd.DataFrame(rows)
        result = detect_network_buckets(rx, drugs, config)
        assert len(result) == 1
        assert result.iloc[0]["risk_bucket"] == "HIGH"
        assert result.iloc[0]["shared_member_count"] == 69

    def test_medium_bucket(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """21-60 shared members => MEDIUM."""
        rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 50.0}
            for i in range(1, 31)
        ]
        rx = pd.DataFrame(rows)
        result = detect_network_buckets(rx, drugs, config)
        assert result.iloc[0]["risk_bucket"] == "MEDIUM"

    def test_low_bucket(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """<=20 shared members => LOW."""
        rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 50.0}
            for i in range(1, 11)
        ]
        rx = pd.DataFrame(rows)
        result = detect_network_buckets(rx, drugs, config)
        assert result.iloc[0]["risk_bucket"] == "LOW"

    def test_non_controlled_excluded(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Non-controlled drugs should not create network edges."""
        rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 1, "drug_id": 3, "paid_amount": 50.0}
            for i in range(1, 100)
        ]
        rx = pd.DataFrame(rows)
        result = detect_network_buckets(rx, drugs, config)
        assert len(result) == 0

    def test_planted_collusive_pair_recall(self, drugs: pd.DataFrame, config: DetectionConfig) -> None:
        """Plant a collusive pair with 65 shared members — must be detected as HIGH."""
        rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 1, "drug_id": 1, "paid_amount": 200.0}
            for i in range(1, 66)
        ]
        # Add noise: other prescribers with low counts
        for i in range(66, 76):
            rows.append({
                "claim_id": i, "member_id": i, "prescriber_id": 2,
                "pharmacy_id": 2, "drug_id": 1, "paid_amount": 50.0,
            })
        rx = pd.DataFrame(rows)
        result = detect_network_buckets(rx, drugs, config)
        high = result[result["risk_bucket"] == "HIGH"]
        assert len(high) >= 1
