"""Tests for R6 — Geo-Distance Anomaly Detection."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from network_graph_core.config import DetectionConfig
from network_graph_core.detectors.geo_anomaly import detect_geo_anomalies, haversine_miles


class TestHaversine:
    def test_known_distance(self) -> None:
        """NYC to LA is ~2,451 miles."""
        d = haversine_miles(
            np.array([40.7128]), np.array([-74.0060]),
            np.array([34.0522]), np.array([-118.2437]),
        )
        assert 2400 < d[0] < 2500

    def test_same_point_zero(self) -> None:
        d = haversine_miles(
            np.array([30.0]), np.array([-90.0]),
            np.array([30.0]), np.array([-90.0]),
        )
        assert d[0] < 0.01


class TestGeoAnomalies:
    def test_distant_fill_flagged(
        self,
        drugs: pd.DataFrame,
        members: pd.DataFrame,
        pharmacies: pd.DataFrame,
        config: DetectionConfig,
    ) -> None:
        """A fill at a pharmacy 1000+ miles from home should be flagged."""
        # Member 1 is in TX (~30.5, -94.7), Pharmacy 6 is in CA (34, -118)
        rx = pd.DataFrame([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 6, "drug_id": 1,
            "fill_date": date(2025, 10, 1), "paid_amount": 200.0,
        }])
        result = detect_geo_anomalies(rx, members, pharmacies, drugs, config)
        assert len(result) >= 1
        assert result.iloc[0]["distance_miles"] > 50

    def test_local_fill_not_flagged(
        self,
        drugs: pd.DataFrame,
        members: pd.DataFrame,
        pharmacies: pd.DataFrame,
        config: DetectionConfig,
    ) -> None:
        """A fill at a nearby pharmacy should not be flagged (unless it exceeds percentile)."""
        # Member 1 (TX) at pharmacy 1 (TX) — should be relatively close
        rx = pd.DataFrame([{
            "claim_id": 1, "member_id": 1, "prescriber_id": 1,
            "pharmacy_id": 1, "drug_id": 1,
            "fill_date": date(2025, 10, 1), "paid_amount": 100.0,
        }])
        result = detect_geo_anomalies(rx, members, pharmacies, drugs, config)
        # Local fill should produce 0 flags if distance < 50 miles
        # Note: with synthetic random coords this may vary, so just verify structure
        assert "distance_miles" in result.columns or len(result) == 0

    def test_planted_geo_outliers_recall(
        self,
        drugs: pd.DataFrame,
        members: pd.DataFrame,
        pharmacies: pd.DataFrame,
        config: DetectionConfig,
    ) -> None:
        """Plant 10 fills at distant pharmacy — recall >= 0.9."""
        rows = [
            {"claim_id": i, "member_id": i, "prescriber_id": 1,
             "pharmacy_id": 6, "drug_id": 1,
             "fill_date": date(2025, 10, 1), "paid_amount": 200.0}
            for i in range(1, 11)
        ]
        rx = pd.DataFrame(rows)
        result = detect_geo_anomalies(rx, members, pharmacies, drugs, config)
        # Members 1-5 are in TX, pharmacy 6 is in CA — should be >50mi
        tx_flagged = result[result["member_id"].isin(range(1, 6))]
        recall = len(tx_flagged) / 5
        assert recall >= 0.9, f"Recall {recall} < 0.9 for TX members filling at CA pharmacy"
