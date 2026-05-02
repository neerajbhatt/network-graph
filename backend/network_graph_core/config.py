"""Configuration management for Network Graph detection engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DetectionConfig:
    """Configuration object passed to all detectors.

    All thresholds are loaded from CONFIG_DETECTION_RULES at runtime.
    This class provides typed access with sensible defaults.
    """

    # R1 — Suspicious fills lookback
    lookback_days_default: int = 30
    lookback_days_by_class: dict[str, int] = field(default_factory=dict)

    # R2 — Network bucket thresholds
    high_threshold: int = 60
    medium_threshold: int = 20

    # R4.2 — Doctor shopping
    doctor_shopping_min_pharmacies: int = 3
    doctor_shopping_min_prescribers: int = 3

    # R4.3 — Pharmacy hubs
    pharmacy_hub_min_prescribers: int = 5

    # R6 — Geo anomaly
    geo_distance_absolute_miles: float = 50.0
    geo_distance_percentile: float = 95.0

    @classmethod
    def from_rules(cls, rules: list[dict[str, Any]]) -> DetectionConfig:
        """Build config from CONFIG_DETECTION_RULES rows.

        Each row has rule_name, parameter_name, parameter_value.
        """
        config = cls()
        lookback_by_class: dict[str, int] = {}

        for rule in rules:
            name = rule.get("rule_name", "")
            param = rule.get("parameter_name", "")
            value = rule.get("parameter_value", "")

            if name == "suspicious_fills" and param == "lookback_days_default":
                config.lookback_days_default = int(value)
            elif name == "suspicious_fills" and param.startswith("lookback_days_"):
                drug_class = param.replace("lookback_days_", "")
                lookback_by_class[drug_class] = int(value)
            elif name == "network_buckets" and param == "high_threshold":
                config.high_threshold = int(value)
            elif name == "network_buckets" and param == "medium_threshold":
                config.medium_threshold = int(value)
            elif name == "doctor_shopping" and param == "min_pharmacies":
                config.doctor_shopping_min_pharmacies = int(value)
            elif name == "doctor_shopping" and param == "min_prescribers":
                config.doctor_shopping_min_prescribers = int(value)
            elif name == "pharmacy_hubs" and param == "min_prescribers":
                config.pharmacy_hub_min_prescribers = int(value)
            elif name == "geo_anomaly" and param == "absolute_miles":
                config.geo_distance_absolute_miles = float(value)
            elif name == "geo_anomaly" and param == "percentile":
                config.geo_distance_percentile = float(value)

        config.lookback_days_by_class = lookback_by_class
        return config

    def get_lookback_days(self, drug_class: str) -> int:
        """Return lookback days for a drug class, falling back to default."""
        return self.lookback_days_by_class.get(drug_class, self.lookback_days_default)
