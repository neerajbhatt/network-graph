"""Tests for DetectionConfig."""

from __future__ import annotations

from network_graph_core.config import DetectionConfig


class TestDetectionConfig:
    def test_defaults(self) -> None:
        config = DetectionConfig()
        assert config.lookback_days_default == 30
        assert config.high_threshold == 60
        assert config.medium_threshold == 20

    def test_from_rules(self) -> None:
        rules = [
            {"rule_name": "suspicious_fills", "parameter_name": "lookback_days_default", "parameter_value": "45"},
            {"rule_name": "suspicious_fills", "parameter_name": "lookback_days_opioids", "parameter_value": "60"},
            {"rule_name": "network_buckets", "parameter_name": "high_threshold", "parameter_value": "80"},
            {"rule_name": "network_buckets", "parameter_name": "medium_threshold", "parameter_value": "30"},
            {"rule_name": "geo_anomaly", "parameter_name": "absolute_miles", "parameter_value": "75"},
        ]
        config = DetectionConfig.from_rules(rules)
        assert config.lookback_days_default == 45
        assert config.high_threshold == 80
        assert config.medium_threshold == 30
        assert config.geo_distance_absolute_miles == 75.0
        assert config.get_lookback_days("opioids") == 60
        assert config.get_lookback_days("unknown_class") == 45
