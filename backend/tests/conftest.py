"""Shared test fixtures for Network Graph detectors."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from network_graph_core.config import DetectionConfig


@pytest.fixture
def config() -> DetectionConfig:
    return DetectionConfig()


@pytest.fixture
def drugs() -> pd.DataFrame:
    return pd.DataFrame([
        {"drug_id": 1, "ndc": "00406-0220-62", "drug_name": "Oxycodone 5mg",
         "drug_class": "opioids", "dea_schedule": "II", "is_controlled": True, "is_commonly_abused": True},
        {"drug_id": 2, "ndc": "00228-2057-11", "drug_name": "Alprazolam 0.25mg",
         "drug_class": "benzodiazepines", "dea_schedule": "IV", "is_controlled": True, "is_commonly_abused": True},
        {"drug_id": 3, "ndc": "00093-1100-01", "drug_name": "Lisinopril 10mg",
         "drug_class": "antihypertensives", "dea_schedule": "NONE",
         "is_controlled": False, "is_commonly_abused": False},
    ])


@pytest.fixture
def members() -> pd.DataFrame:
    """10 test members across 2 states."""
    rows = []
    for i in range(1, 11):
        lat = 30.0 + i * 0.5 if i <= 5 else 40.0 + (i - 5) * 0.5
        lon = -95.0 + i * 0.3 if i <= 5 else -75.0 + (i - 5) * 0.3
        rows.append({
            "member_id": i,
            "member_name": f"Member {i}",
            "state": "TX" if i <= 5 else "NY",
            "zip": f"{70000 + i:05d}",
            "latitude": lat,
            "longitude": lon,
        })
    return pd.DataFrame(rows)


@pytest.fixture
def prescribers() -> pd.DataFrame:
    rows = []
    for i in range(1, 6):
        rows.append({
            "prescriber_id": i,
            "npi": f"100000000{i}",
            "prescriber_name": f"Dr. Test{i}",
            "specialty": "Pain Management" if i <= 2 else "Internal Medicine",
            "state": "TX" if i <= 3 else "NY",
            "latitude": 30.0 + i * 0.1,
            "longitude": -95.0 + i * 0.1,
        })
    return pd.DataFrame(rows)


@pytest.fixture
def pharmacies() -> pd.DataFrame:
    rows = []
    for i in range(1, 6):
        rows.append({
            "pharmacy_id": i,
            "npi": f"200000000{i}",
            "pharmacy_name": f"Pharmacy {i}",
            "state": "TX" if i <= 3 else "NY",
            "latitude": 30.0 + i * 0.2,
            "longitude": -95.0 + i * 0.2,
        })
    # Add a distant pharmacy for geo tests
    rows.append({
        "pharmacy_id": 6,
        "npi": "2000000006",
        "pharmacy_name": "Distant Pharmacy",
        "state": "CA",
        "latitude": 34.0,
        "longitude": -118.0,
    })
    return pd.DataFrame(rows)


@pytest.fixture
def base_date() -> date:
    return date(2025, 10, 1)
