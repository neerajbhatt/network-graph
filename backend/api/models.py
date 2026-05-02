"""Pydantic response models for the Network Graph API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


# --- Pagination ---
class PaginatedResponse(BaseModel):
    total: int
    offset: int
    limit: int
    data: list[Any]


# --- Network Graph ---
class NetworkNode(BaseModel):
    id: str
    label: str
    type: str  # "prescriber" | "pharmacy"
    npi: str | None = None
    specialty: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class NetworkEdge(BaseModel):
    source: str
    target: str
    shared_member_count: int
    risk_bucket: str
    total_exposure: float


class NetworkGraphResponse(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    total_edges: int


# --- Drill-down ---
class DrillMember(BaseModel):
    member_id: int
    member_name: str  # PHI
    fills: list[DrillFill]


class DrillFill(BaseModel):
    claim_id: int
    drug_name: str
    ndc: str
    fill_date: date
    days_supply: int | None = None
    quantity: int | None = None
    paid_amount: float


DrillMember.model_rebuild()


class DrillResponse(BaseModel):
    prescriber_id: int | None = None
    prescriber_name: str | None = None
    pharmacy_id: int | None = None
    pharmacy_name: str | None = None
    members: list[DrillMember]


# --- Doctor Shoppers ---
class DoctorShopper(BaseModel):
    member_id: int
    member_name: str | None = None  # PHI
    member_state: str | None = None
    pharmacy_count: int
    prescriber_count: int
    controlled_fill_count: int
    total_exposure: float
    risk_bucket: str
    first_fill_date: date | None = None
    last_fill_date: date | None = None


# --- Pharmacy Hubs ---
class PharmacyHub(BaseModel):
    pharmacy_id: int
    pharmacy_name: str | None = None
    pharmacy_npi: str | None = None
    pharmacy_state: str | None = None
    distinct_prescriber_count: int
    distinct_member_count: int
    total_claims: int
    total_exposure: float
    risk_bucket: str


# --- Geo Outliers ---
class GeoOutlier(BaseModel):
    claim_id: int
    member_id: int
    member_name: str | None = None  # PHI
    member_state: str | None = None
    member_zip: str | None = None
    pharmacy_id: int
    pharmacy_name: str | None = None
    pharmacy_state: str | None = None
    pharmacy_zip: str | None = None
    drug_name: str | None = None
    drug_class: str | None = None
    fill_date: date | None = None
    paid_amount: float
    distance_miles: float
    risk_bucket: str
    member_lat: float | None = None
    member_lon: float | None = None
    pharmacy_lat: float | None = None
    pharmacy_lon: float | None = None


# --- Config ---
class ConfigRule(BaseModel):
    rule_id: int | None = None
    rule_name: str
    parameter_name: str
    parameter_value: str
    description: str | None = None
    updated_at: datetime | None = None


class ConfigRuleUpdate(BaseModel):
    rules: list[ConfigRule]


# --- KPI ---
class KpiSummary(BaseModel):
    total_claims: int
    total_exposure: float
    total_members: int
    total_flagged: int


# --- Health ---
class HealthResponse(BaseModel):
    status: str
    version: str
    data_mode: str
