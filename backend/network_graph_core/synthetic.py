"""Synthetic data generator for Network Graph.

Generates reproducible synthetic data with planted fraud patterns:
- 10,000 members, 500 prescribers, 200 pharmacies, 6 months of claims
- ~5% planted fraud: doctor shoppers, collusive prescriber-pharmacy pairs, geo-outliers

Usage:
    python -m network_graph_core.synthetic --output-dir data/synthetic
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# Seed for reproducibility
SEED = 42
fake = Faker("en_US")
Faker.seed(SEED)
rng = np.random.default_rng(SEED)

# --- Constants ---
N_MEMBERS = 10_000
N_PRESCRIBERS = 500
N_PHARMACIES = 200
DATE_START = date(2025, 7, 1)
DATE_END = date(2025, 12, 31)
N_DAYS = (DATE_END - DATE_START).days

# Fraud planting rates
N_DOCTOR_SHOPPERS = 150  # ~1.5% of members
N_COLLUSIVE_PAIRS = 15   # prescriber-pharmacy pairs
N_GEO_OUTLIER_MEMBERS = 100  # members who fill far from home

# US states with approximate lat/lon ranges for realistic zip generation
STATES = [
    ("TX", 26.0, 36.5, -106.6, -93.5),
    ("CA", 32.5, 42.0, -124.4, -114.1),
    ("FL", 24.5, 31.0, -87.6, -80.0),
    ("NY", 40.5, 45.0, -79.8, -71.8),
    ("PA", 39.7, 42.3, -80.5, -74.7),
    ("IL", 37.0, 42.5, -91.5, -87.5),
    ("OH", 38.4, 42.0, -84.8, -80.5),
    ("GA", 30.4, 35.0, -85.6, -80.8),
    ("NC", 33.8, 36.6, -84.3, -75.5),
    ("MI", 41.7, 48.3, -90.4, -82.1),
]

SPECIALTIES = [
    "Internal Medicine", "Family Medicine", "Pain Management",
    "Orthopedic Surgery", "Neurology", "Psychiatry",
    "Emergency Medicine", "General Practice", "Anesthesiology",
    "Physical Medicine", "Dentistry", "Oral Surgery",
]

PHARMACY_TYPES = ["Retail", "Chain", "Independent", "Mail Order", "Specialty"]

DRUG_CLASSES = ["opioids", "benzodiazepines", "stimulants", "gabapentinoids", "muscle_relaxants", "sedatives"]

# Representative NDCs per class (matching seed data)
DRUG_DATA = [
    ("00406-0220-62", "Oxycodone HCl 5mg", "opioids", "II", True, True),
    ("00406-0222-62", "Oxycodone HCl 10mg", "opioids", "II", True, True),
    ("00406-0224-62", "Oxycodone HCl 15mg", "opioids", "II", True, True),
    ("63481-0623-70", "Hydrocodone-APAP 5/325mg", "opioids", "II", True, True),
    ("63481-0624-70", "Hydrocodone-APAP 7.5/325mg", "opioids", "II", True, True),
    ("63481-0625-70", "Hydrocodone-APAP 10/325mg", "opioids", "II", True, True),
    ("00591-3535-01", "Morphine Sulfate 15mg", "opioids", "II", True, True),
    ("00591-3536-01", "Morphine Sulfate 30mg", "opioids", "II", True, True),
    ("00406-1220-62", "Hydromorphone 2mg", "opioids", "II", True, True),
    ("00591-2830-01", "Fentanyl 25mcg/hr Patch", "opioids", "II", True, True),
    ("00093-5250-01", "Tramadol 50mg", "opioids", "IV", True, True),
    ("12496-1206-01", "Buprenorphine-Naloxone 8/2mg", "opioids", "III", True, True),
    ("00228-2057-11", "Alprazolam 0.25mg", "benzodiazepines", "IV", True, True),
    ("00228-2058-11", "Alprazolam 0.5mg", "benzodiazepines", "IV", True, True),
    ("00228-2059-11", "Alprazolam 1mg", "benzodiazepines", "IV", True, True),
    ("00228-2060-11", "Alprazolam 2mg", "benzodiazepines", "IV", True, True),
    ("00781-1064-01", "Lorazepam 0.5mg", "benzodiazepines", "IV", True, True),
    ("00781-1065-01", "Lorazepam 1mg", "benzodiazepines", "IV", True, True),
    ("00093-8108-01", "Diazepam 5mg", "benzodiazepines", "IV", True, True),
    ("00093-5340-01", "Clonazepam 0.5mg", "benzodiazepines", "IV", True, True),
    ("00093-5341-01", "Clonazepam 1mg", "benzodiazepines", "IV", True, True),
    ("00555-0764-02", "Amphetamine Salts 10mg", "stimulants", "II", True, True),
    ("00555-0766-02", "Amphetamine Salts 20mg", "stimulants", "II", True, True),
    ("00555-0768-02", "Amphetamine Salts 30mg", "stimulants", "II", True, True),
    ("57844-0110-01", "Adderall XR 10mg", "stimulants", "II", True, True),
    ("57844-0120-01", "Adderall XR 20mg", "stimulants", "II", True, True),
    ("00406-1010-01", "Methylphenidate 10mg", "stimulants", "II", True, True),
    ("00406-1020-01", "Methylphenidate 20mg", "stimulants", "II", True, True),
    ("27241-0050-05", "Gabapentin 100mg", "gabapentinoids", "V", True, True),
    ("27241-0051-05", "Gabapentin 300mg", "gabapentinoids", "V", True, True),
    ("27241-0052-05", "Gabapentin 400mg", "gabapentinoids", "V", True, True),
    ("27241-0053-05", "Gabapentin 600mg", "gabapentinoids", "V", True, True),
    ("00071-1013-68", "Pregabalin (Lyrica) 50mg", "gabapentinoids", "V", True, True),
    ("00071-1014-68", "Pregabalin (Lyrica) 75mg", "gabapentinoids", "V", True, True),
    ("00071-1015-68", "Pregabalin (Lyrica) 150mg", "gabapentinoids", "V", True, True),
    ("00228-2100-11", "Carisoprodol (Soma) 250mg", "muscle_relaxants", "IV", True, True),
    ("00228-2101-11", "Carisoprodol (Soma) 350mg", "muscle_relaxants", "IV", True, True),
    ("00591-5513-01", "Cyclobenzaprine 5mg", "muscle_relaxants", "NONE", False, True),
    ("00591-5514-01", "Cyclobenzaprine 10mg", "muscle_relaxants", "NONE", False, True),
    ("00093-0089-01", "Zolpidem (Ambien) 5mg", "sedatives", "IV", True, True),
    ("00093-0090-01", "Zolpidem (Ambien) 10mg", "sedatives", "IV", True, True),
    # Non-controlled common drugs for noise
    ("00093-1100-01", "Lisinopril 10mg", "antihypertensives", "NONE", False, False),
    ("00093-1101-01", "Lisinopril 20mg", "antihypertensives", "NONE", False, False),
    ("00093-7180-01", "Metformin 500mg", "antidiabetics", "NONE", False, False),
    ("00093-7181-01", "Metformin 1000mg", "antidiabetics", "NONE", False, False),
    ("00093-0150-01", "Atorvastatin 10mg", "statins", "NONE", False, False),
    ("00093-0151-01", "Atorvastatin 20mg", "statins", "NONE", False, False),
    ("00093-5160-01", "Amlodipine 5mg", "antihypertensives", "NONE", False, False),
    ("00093-5161-01", "Amlodipine 10mg", "antihypertensives", "NONE", False, False),
    ("00093-3145-01", "Omeprazole 20mg", "ppis", "NONE", False, False),
    ("00093-3146-01", "Omeprazole 40mg", "ppis", "NONE", False, False),
]


def _random_location(state_info: tuple[str, float, float, float, float]) -> tuple[str, str, float, float]:
    """Generate random city, zip, lat, lon within a state's bounds."""
    state, lat_min, lat_max, lon_min, lon_max = state_info
    lat = rng.uniform(lat_min, lat_max)
    lon = rng.uniform(lon_min, lon_max)
    zip_code = f"{rng.integers(10000, 99999):05d}"
    city = fake.city()
    return city, zip_code, lat, lon


def generate_members() -> pd.DataFrame:
    """Generate DIM_MEMBER with 10,000 members."""  # PHI fields marked
    rows = []
    for i in range(1, N_MEMBERS + 1):
        state_info = STATES[rng.integers(0, len(STATES))]
        city, zip_code, lat, lon = _random_location(state_info)
        gender = rng.choice(["M", "F"])
        profile = fake.profile(sex="M" if gender == "M" else "F")
        dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
        enroll_start = fake.date_between(start_date="-3y", end_date="-1y")
        rows.append({
            "member_id": i,
            "member_name": profile["name"],          # PHI
            "dob": dob,                               # PHI
            "gender": gender,
            "address": fake.street_address(),          # PHI
            "city": city,
            "state": state_info[0],
            "zip": zip_code,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "enrollment_start": enroll_start,
            "enrollment_end": enroll_start + timedelta(days=int(rng.integers(365, 1095))),
        })
    return pd.DataFrame(rows)


def generate_prescribers() -> pd.DataFrame:
    """Generate DIM_PRESCRIBER with 500 prescribers."""
    rows = []
    for i in range(1, N_PRESCRIBERS + 1):
        state_info = STATES[rng.integers(0, len(STATES))]
        city, zip_code, lat, lon = _random_location(state_info)
        rows.append({
            "prescriber_id": i,
            "npi": f"{1000000000 + i}",
            "prescriber_name": f"Dr. {fake.last_name()}",
            "specialty": rng.choice(SPECIALTIES),
            "address": fake.street_address(),
            "city": city,
            "state": state_info[0],
            "zip": zip_code,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
        })
    return pd.DataFrame(rows)


def generate_pharmacies() -> pd.DataFrame:
    """Generate DIM_PHARMACY with 200 pharmacies."""
    rows = []
    names = ["CVS", "Walgreens", "Rite Aid", "Walmart", "Costco",
             "Kroger", "HEB", "Publix", "Winn-Dixie", "Medicine Shoppe"]
    for i in range(1, N_PHARMACIES + 1):
        state_info = STATES[rng.integers(0, len(STATES))]
        city, zip_code, lat, lon = _random_location(state_info)
        base_name = rng.choice(names)
        rows.append({
            "pharmacy_id": i,
            "npi": f"{2000000000 + i}",
            "pharmacy_name": f"{base_name} #{rng.integers(100, 9999)}",
            "pharmacy_type": rng.choice(PHARMACY_TYPES),
            "address": fake.street_address(),
            "city": city,
            "state": state_info[0],
            "zip": zip_code,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
        })
    return pd.DataFrame(rows)


def generate_drugs() -> pd.DataFrame:
    """Generate DIM_DRUG from DRUG_DATA."""
    rows = []
    for i, (ndc, name, cls, sched, controlled, abused) in enumerate(DRUG_DATA, 1):
        rows.append({
            "drug_id": i,
            "ndc": ndc,
            "drug_name": name,
            "drug_class": cls,
            "dea_schedule": sched,
            "is_controlled": controlled,
            "is_commonly_abused": abused,
        })
    return pd.DataFrame(rows)


def generate_pharmacy_claims(
    members: pd.DataFrame,
    prescribers: pd.DataFrame,
    pharmacies: pd.DataFrame,
    drugs: pd.DataFrame,
) -> pd.DataFrame:
    """Generate FACT_PHARMACY_CLAIM with planted fraud patterns."""
    controlled_drug_ids = drugs[drugs["is_controlled"] | drugs["is_commonly_abused"]]["drug_id"].values
    all_drug_ids = drugs["drug_id"].values
    member_ids = members["member_id"].values
    prescriber_ids = prescribers["prescriber_id"].values
    pharmacy_ids = pharmacies["pharmacy_id"].values

    claims: list[dict] = []
    claim_id = 1

    # --- Normal claims (~25,000) ---
    for _ in range(25_000):
        fill_offset = rng.integers(0, N_DAYS)
        is_controlled = rng.random() < 0.3
        drug_id = int(rng.choice(controlled_drug_ids if is_controlled else all_drug_ids))
        claims.append({
            "claim_id": claim_id,
            "member_id": int(rng.choice(member_ids)),
            "prescriber_id": int(rng.choice(prescriber_ids)),
            "pharmacy_id": int(rng.choice(pharmacy_ids)),
            "drug_id": drug_id,
            "fill_date": DATE_START + timedelta(days=int(fill_offset)),
            "days_supply": int(rng.choice([7, 14, 30, 60, 90])),
            "quantity": int(rng.choice([30, 60, 90, 120, 180])),
            "paid_amount": round(float(rng.uniform(10, 500)), 2),
            "claim_status": "PAID",
        })
        claim_id += 1

    # --- Planted: Doctor shoppers (~150 members, each filling at 4-8 pharmacies) ---
    shopper_member_ids = rng.choice(member_ids, size=N_DOCTOR_SHOPPERS, replace=False)
    for mid in shopper_member_ids:
        n_pharmacies = rng.integers(4, 9)
        n_prescribers = rng.integers(4, 9)
        pharm_subset = rng.choice(pharmacy_ids, size=min(n_pharmacies, len(pharmacy_ids)), replace=False)
        presc_subset = rng.choice(prescriber_ids, size=min(n_prescribers, len(prescriber_ids)), replace=False)
        n_fills = rng.integers(8, 20)
        for _ in range(n_fills):
            fill_offset = rng.integers(0, N_DAYS)
            claims.append({
                "claim_id": claim_id,
                "member_id": int(mid),
                "prescriber_id": int(rng.choice(presc_subset)),
                "pharmacy_id": int(rng.choice(pharm_subset)),
                "drug_id": int(rng.choice(controlled_drug_ids)),
                "fill_date": DATE_START + timedelta(days=int(fill_offset)),
                "days_supply": int(rng.choice([7, 14, 30])),
                "quantity": int(rng.choice([60, 90, 120, 180])),
                "paid_amount": round(float(rng.uniform(50, 800)), 2),
                "claim_status": "PAID",
            })
            claim_id += 1

    # --- Planted: Collusive prescriber-pharmacy pairs (15 pairs, each sharing 40-80 members) ---
    for _ in range(N_COLLUSIVE_PAIRS):
        presc_id = int(rng.choice(prescriber_ids))
        pharm_id = int(rng.choice(pharmacy_ids))
        shared_count = rng.integers(40, 81)
        shared_members = rng.choice(member_ids, size=shared_count, replace=False)
        for mid in shared_members:
            n_fills = rng.integers(1, 4)
            for _ in range(n_fills):
                fill_offset = rng.integers(0, N_DAYS)
                claims.append({
                    "claim_id": claim_id,
                    "member_id": int(mid),
                    "prescriber_id": presc_id,
                    "pharmacy_id": pharm_id,
                    "drug_id": int(rng.choice(controlled_drug_ids)),
                    "fill_date": DATE_START + timedelta(days=int(fill_offset)),
                    "days_supply": int(rng.choice([7, 14, 30])),
                    "quantity": int(rng.choice([30, 60, 90, 120])),
                    "paid_amount": round(float(rng.uniform(50, 600)), 2),
                    "claim_status": "PAID",
                })
                claim_id += 1

    # --- Planted: Geo-outlier fills (100 members filling 200+ miles from home) ---
    geo_outlier_members = rng.choice(member_ids, size=N_GEO_OUTLIER_MEMBERS, replace=False)
    # Pick pharmacies in distant states
    for mid in geo_outlier_members:
        member_row = members[members["member_id"] == int(mid)].iloc[0]
        member_state = member_row["state"]
        # Pick a pharmacy in a different state
        distant_pharmacies = pharmacies[pharmacies["state"] != member_state]
        if len(distant_pharmacies) == 0:
            distant_pharmacies = pharmacies
        pharm_id = int(distant_pharmacies.sample(1, random_state=int(mid))["pharmacy_id"].values[0])
        n_fills = rng.integers(2, 6)
        for _ in range(n_fills):
            fill_offset = rng.integers(0, N_DAYS)
            claims.append({
                "claim_id": claim_id,
                "member_id": int(mid),
                "prescriber_id": int(rng.choice(prescriber_ids)),
                "pharmacy_id": pharm_id,
                "drug_id": int(rng.choice(controlled_drug_ids)),
                "fill_date": DATE_START + timedelta(days=int(fill_offset)),
                "days_supply": int(rng.choice([7, 14, 30])),
                "quantity": int(rng.choice([60, 90, 120])),
                "paid_amount": round(float(rng.uniform(100, 1000)), 2),
                "claim_status": "PAID",
            })
            claim_id += 1

    return pd.DataFrame(claims)


def generate_medical_claims(
    members: pd.DataFrame,
    prescribers: pd.DataFrame,
) -> pd.DataFrame:
    """Generate FACT_MEDICAL_CLAIM.

    Most members have some medical visits; doctor shoppers intentionally have gaps.
    """
    member_ids = members["member_id"].values
    prescriber_ids = prescribers["prescriber_id"].values
    claims: list[dict] = []
    claim_id = 1

    # Normal members get 1-4 medical visits in the period
    for mid in member_ids:
        n_visits = rng.integers(0, 5)
        for _ in range(n_visits):
            offset = rng.integers(0, N_DAYS)
            claims.append({
                "claim_id": claim_id,
                "member_id": int(mid),
                "prescriber_id": int(rng.choice(prescriber_ids)),
                "service_date": DATE_START + timedelta(days=int(offset)),
                "procedure_code": f"9920{rng.integers(1, 5)}",
                "diagnosis_code": rng.choice(["M54.5", "G89.4", "F41.1", "J06.9", "R10.9"]),
                "place_of_service": rng.choice(["Office", "Outpatient", "ER", "Telehealth"]),
                "paid_amount": round(float(rng.uniform(50, 300)), 2),
                "claim_status": "PAID",
            })
            claim_id += 1

    return pd.DataFrame(claims)


def generate_dental_claims(
    members: pd.DataFrame,
    prescribers: pd.DataFrame,
) -> pd.DataFrame:
    """Generate FACT_DENTAL_CLAIM — sparser than medical."""
    member_ids = members["member_id"].values
    # Only dental-specialty prescribers
    dental_prescriber_ids = prescribers[
        prescribers["specialty"].isin(["Dentistry", "Oral Surgery"])
    ]["prescriber_id"].values
    if len(dental_prescriber_ids) == 0:
        dental_prescriber_ids = prescribers["prescriber_id"].values[:20]

    claims: list[dict] = []
    claim_id = 1

    # ~30% of members have a dental visit
    dental_members = rng.choice(member_ids, size=int(len(member_ids) * 0.3), replace=False)
    for mid in dental_members:
        n_visits = rng.integers(1, 3)
        for _ in range(n_visits):
            offset = rng.integers(0, N_DAYS)
            claims.append({
                "claim_id": claim_id,
                "member_id": int(mid),
                "prescriber_id": int(rng.choice(dental_prescriber_ids)),
                "service_date": DATE_START + timedelta(days=int(offset)),
                "procedure_code": rng.choice(["D0120", "D0274", "D2750", "D7140", "D7210"]),
                "diagnosis_code": rng.choice(["K02.9", "K05.1", "K08.1"]),
                "paid_amount": round(float(rng.uniform(75, 500)), 2),
                "claim_status": "PAID",
            })
            claim_id += 1

    return pd.DataFrame(claims)


def generate_all(output_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Generate all synthetic data and write to CSVs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating members...")
    members = generate_members()

    print("Generating prescribers...")
    prescribers = generate_prescribers()

    print("Generating pharmacies...")
    pharmacies = generate_pharmacies()

    print("Generating drugs...")
    drugs = generate_drugs()

    print("Generating pharmacy claims (with planted fraud)...")
    pharmacy_claims = generate_pharmacy_claims(members, prescribers, pharmacies, drugs)

    print("Generating medical claims...")
    medical_claims = generate_medical_claims(members, prescribers)

    print("Generating dental claims...")
    dental_claims = generate_dental_claims(members, prescribers)

    datasets = {
        "dim_member": members,
        "dim_prescriber": prescribers,
        "dim_pharmacy": pharmacies,
        "dim_drug": drugs,
        "fact_pharmacy_claim": pharmacy_claims,
        "fact_medical_claim": medical_claims,
        "fact_dental_claim": dental_claims,
    }

    for name, df in datasets.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  {name}: {len(df):,} rows -> {path}")

    print(f"\nTotal pharmacy claims: {len(pharmacy_claims):,}")
    print(f"  Approximate fraud patterns: ~{N_DOCTOR_SHOPPERS} doctor shoppers, "
          f"~{N_COLLUSIVE_PAIRS} collusive pairs, ~{N_GEO_OUTLIER_MEMBERS} geo-outliers")

    return datasets


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Network Graph data")
    parser.add_argument("--output-dir", default="data/synthetic", help="Output directory")
    args = parser.parse_args()
    generate_all(args.output_dir)


if __name__ == "__main__":
    main()
