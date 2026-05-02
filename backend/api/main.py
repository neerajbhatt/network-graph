"""FastAPI application for Network Graph."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Any

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.database import execute, query_df
from api.models import (
    ConfigRule,
    ConfigRuleUpdate,
    DoctorShopper,
    DrillFill,
    DrillMember,
    DrillResponse,
    GeoOutlier,
    HealthResponse,
    KpiSummary,
    NetworkEdge,
    NetworkGraphResponse,
    NetworkNode,
    PaginatedResponse,
    PharmacyHub,
)

# PHI fields excluded from logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("network_graph")

KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", "780"))  # 13 minutes
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://network-graph-web.onrender.com")
BACKEND_URL = os.getenv("BACKEND_URL", "https://network-graph-api-q6hf.onrender.com")


async def _keep_alive_loop() -> None:
    """Ping frontend and backend every 13 minutes to prevent Render free-tier sleep."""
    await asyncio.sleep(60)  # wait for startup
    while True:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r1 = await client.get(f"{BACKEND_URL}/api/network-graph/healthz")
                logger.info("keep-alive: backend %s", r1.status_code)
                r2 = await client.get(FRONTEND_URL)
                logger.info("keep-alive: frontend %s", r2.status_code)
        except Exception as exc:
            logger.warning("keep-alive ping failed: %s", exc)
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[no-untyped-def]
    task = asyncio.create_task(_keep_alive_loop())
    yield
    task.cancel()


app = FastAPI(
    title="Network Graph API",
    description="Pharmacy Fraud & Abuse Detection Platform",
    version="0.1.0",
    root_path="/api/network-graph",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_MODE = os.getenv("DATA_MODE", "SYNTHETIC")


# --- Health ---
@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0", data_mode=DATA_MODE)


# --- KPI ---
@app.get("/kpi", response_model=KpiSummary)
def get_kpi() -> KpiSummary:
    df = query_df("""
        SELECT
            COUNT(DISTINCT fc.claim_id) AS total_claims,
            COALESCE(SUM(fc.paid_amount), 0) AS total_exposure,
            COUNT(DISTINCT fc.member_id) AS total_members,
            (SELECT COUNT(*) FROM network_graph.fact_suspicious_fill) AS total_flagged
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
    """)
    row = df.iloc[0]
    return KpiSummary(
        total_claims=int(row["total_claims"]),
        total_exposure=float(row["total_exposure"]),
        total_members=int(row["total_members"]),
        total_flagged=int(row["total_flagged"]),
    )


# --- Networks ---
@app.get("/networks", response_model=NetworkGraphResponse)
def get_networks(
    bucket: str | None = Query(None, description="Risk bucket filter: HIGH, MEDIUM, LOW"),
    drug_class: str | None = Query(None),
    state: str | None = Query(None),
    specialty: str | None = Query(None),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    min_shared: int = Query(1, ge=1),
    limit: int = Query(200, ge=1, le=1000),
) -> NetworkGraphResponse:
    where_clauses = ["(d.is_controlled = TRUE OR d.is_commonly_abused = TRUE)"]
    params: dict[str, Any] = {}

    if drug_class:
        where_clauses.append("d.drug_class = :drug_class")
        params["drug_class"] = drug_class
    if state:
        where_clauses.append("(pr.state = :state OR ph.state = :state)")
        params["state"] = state
    if specialty:
        where_clauses.append("pr.specialty = :specialty")
        params["specialty"] = specialty
    if date_from:
        where_clauses.append("fc.fill_date >= :date_from")
        params["date_from"] = date_from.isoformat()
    if date_to:
        where_clauses.append("fc.fill_date <= :date_to")
        params["date_to"] = date_to.isoformat()

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            pr.prescriber_id, pr.prescriber_name, pr.npi AS prescriber_npi,
            pr.specialty, pr.state AS prescriber_state,
            pr.latitude AS prescriber_lat, pr.longitude AS prescriber_lon,
            ph.pharmacy_id, ph.pharmacy_name, ph.npi AS pharmacy_npi,
            ph.state AS pharmacy_state,
            ph.latitude AS pharmacy_lat, ph.longitude AS pharmacy_lon,
            COUNT(DISTINCT fc.member_id) AS shared_member_count,
            SUM(fc.paid_amount) AS total_exposure
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_prescriber pr ON fc.prescriber_id = pr.prescriber_id
        JOIN network_graph.dim_pharmacy ph ON fc.pharmacy_id = ph.pharmacy_id
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE {where_sql}
        GROUP BY pr.prescriber_id, pr.prescriber_name, pr.npi, pr.specialty,
                 pr.state, pr.latitude, pr.longitude,
                 ph.pharmacy_id, ph.pharmacy_name, ph.npi, ph.state,
                 ph.latitude, ph.longitude
        HAVING COUNT(DISTINCT fc.member_id) >= :min_shared
        ORDER BY shared_member_count DESC
        LIMIT :limit
    """
    params["min_shared"] = min_shared
    params["limit"] = limit

    df = query_df(sql, params)

    # Load config thresholds
    cfg = query_df("""
        SELECT parameter_name, parameter_value
        FROM network_graph.config_detection_rules
        WHERE rule_name = 'network_buckets'
    """)
    high_t = 60
    med_t = 20
    for _, r in cfg.iterrows():
        if r["parameter_name"] == "high_threshold":
            high_t = int(r["parameter_value"])
        elif r["parameter_name"] == "medium_threshold":
            med_t = int(r["parameter_value"])

    nodes_map: dict[str, NetworkNode] = {}
    edges: list[NetworkEdge] = []

    for _, row in df.iterrows():
        count = int(row["shared_member_count"])
        if count > high_t:
            rb = "HIGH"
        elif count > med_t:
            rb = "MEDIUM"
        else:
            rb = "LOW"

        if bucket and rb != bucket:
            continue

        pr_key = f"prescriber_{row['prescriber_id']}"
        ph_key = f"pharmacy_{row['pharmacy_id']}"

        if pr_key not in nodes_map:
            nodes_map[pr_key] = NetworkNode(
                id=pr_key,
                label=str(row["prescriber_name"]),
                type="prescriber",
                npi=str(row["prescriber_npi"]),
                specialty=str(row.get("specialty", "")),
                state=str(row.get("prescriber_state", "")),
                latitude=float(row["prescriber_lat"]) if pd.notna(row.get("prescriber_lat")) else None,
                longitude=float(row["prescriber_lon"]) if pd.notna(row.get("prescriber_lon")) else None,
            )
        if ph_key not in nodes_map:
            nodes_map[ph_key] = NetworkNode(
                id=ph_key,
                label=str(row["pharmacy_name"]),
                type="pharmacy",
                npi=str(row["pharmacy_npi"]),
                state=str(row.get("pharmacy_state", "")),
                latitude=float(row["pharmacy_lat"]) if pd.notna(row.get("pharmacy_lat")) else None,
                longitude=float(row["pharmacy_lon"]) if pd.notna(row.get("pharmacy_lon")) else None,
            )

        edges.append(NetworkEdge(
            source=pr_key,
            target=ph_key,
            shared_member_count=count,
            risk_bucket=rb,
            total_exposure=round(float(row["total_exposure"]), 2),
        ))

    return NetworkGraphResponse(
        nodes=list(nodes_map.values()),
        edges=edges,
        total_edges=len(edges),
    )


# --- Network Drill ---
@app.get("/networks/{network_id}/drill", response_model=DrillResponse)
def drill_network(network_id: str) -> DrillResponse:
    parts = network_id.split("_", 1)
    if len(parts) != 2:
        raise HTTPException(400, "Invalid network_id format. Use prescriber_123 or pharmacy_456.")

    node_type, node_id_str = parts
    try:
        node_id = int(node_id_str)
    except ValueError:
        raise HTTPException(400, "Invalid node ID.")

    if node_type == "prescriber":
        id_col = "fc.prescriber_id"
    elif node_type == "pharmacy":
        id_col = "fc.pharmacy_id"
    else:
        raise HTTPException(400, "Node type must be prescriber or pharmacy.")

    sql = f"""
        SELECT
            m.member_id, m.member_name,
            fc.claim_id, d.drug_name, d.ndc, fc.fill_date,
            fc.days_supply, fc.quantity, fc.paid_amount
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_member m ON fc.member_id = m.member_id
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE {id_col} = :node_id
            AND (d.is_controlled = TRUE OR d.is_commonly_abused = TRUE)
        ORDER BY m.member_id, fc.fill_date
        LIMIT 500
    """
    df = query_df(sql, {"node_id": node_id})

    members_dict: dict[int, DrillMember] = {}
    for _, row in df.iterrows():
        mid = int(row["member_id"])
        if mid not in members_dict:
            members_dict[mid] = DrillMember(
                member_id=mid,
                member_name=str(row["member_name"]),  # PHI
                fills=[],
            )
        members_dict[mid].fills.append(DrillFill(
            claim_id=int(row["claim_id"]),
            drug_name=str(row["drug_name"]),
            ndc=str(row["ndc"]),
            fill_date=row["fill_date"],
            days_supply=int(row["days_supply"]) if pd.notna(row.get("days_supply")) else None,
            quantity=int(row["quantity"]) if pd.notna(row.get("quantity")) else None,
            paid_amount=float(row["paid_amount"]),
        ))

    # Get node info
    prescriber_id = node_id if node_type == "prescriber" else None
    pharmacy_id = node_id if node_type == "pharmacy" else None
    prescriber_name = None
    pharmacy_name = None

    if prescriber_id:
        info = query_df(
            "SELECT prescriber_name FROM network_graph.dim_prescriber WHERE prescriber_id = :id",
            {"id": prescriber_id},
        )
        if len(info):
            prescriber_name = str(info.iloc[0]["prescriber_name"])
    if pharmacy_id:
        info = query_df(
            "SELECT pharmacy_name FROM network_graph.dim_pharmacy WHERE pharmacy_id = :id",
            {"id": pharmacy_id},
        )
        if len(info):
            pharmacy_name = str(info.iloc[0]["pharmacy_name"])

    return DrillResponse(
        prescriber_id=prescriber_id,
        prescriber_name=prescriber_name,
        pharmacy_id=pharmacy_id,
        pharmacy_name=pharmacy_name,
        members=list(members_dict.values()),
    )


# --- Doctor Shoppers ---
@app.get("/doctor-shoppers", response_model=PaginatedResponse)
def get_doctor_shoppers(
    min_pharmacies: int = Query(3, ge=1),
    min_prescribers: int = Query(3, ge=1),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse:
    where = ["(d.is_controlled = TRUE OR d.is_commonly_abused = TRUE)"]
    params: dict[str, Any] = {}
    if date_from:
        where.append("fc.fill_date >= :date_from")
        params["date_from"] = date_from.isoformat()
    if date_to:
        where.append("fc.fill_date <= :date_to")
        params["date_to"] = date_to.isoformat()

    where_sql = " AND ".join(where)

    sql = f"""
        SELECT
            m.member_id, m.member_name, m.state AS member_state,
            COUNT(DISTINCT fc.pharmacy_id) AS pharmacy_count,
            COUNT(DISTINCT fc.prescriber_id) AS prescriber_count,
            COUNT(fc.claim_id) AS controlled_fill_count,
            SUM(fc.paid_amount) AS total_exposure,
            CASE
                WHEN COUNT(DISTINCT fc.pharmacy_id) >= 5 OR COUNT(DISTINCT fc.prescriber_id) >= 5 THEN 'HIGH'
                WHEN COUNT(DISTINCT fc.pharmacy_id) >= 3 OR COUNT(DISTINCT fc.prescriber_id) >= 3 THEN 'MEDIUM'
                ELSE 'LOW'
            END AS risk_bucket,
            MIN(fc.fill_date) AS first_fill_date,
            MAX(fc.fill_date) AS last_fill_date
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_member m ON fc.member_id = m.member_id
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE {where_sql}
        GROUP BY m.member_id, m.member_name, m.state
        HAVING COUNT(DISTINCT fc.pharmacy_id) >= :min_pharm
            OR COUNT(DISTINCT fc.prescriber_id) >= :min_presc
        ORDER BY total_exposure DESC
        LIMIT :limit OFFSET :offset
    """
    params["min_pharm"] = min_pharmacies
    params["min_presc"] = min_prescribers
    params["limit"] = limit
    params["offset"] = offset

    df = query_df(sql, params)

    # Count total
    count_sql = f"""
        SELECT COUNT(*) AS cnt FROM (
            SELECT fc.member_id
            FROM network_graph.fact_pharmacy_claim fc
            JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
            WHERE {where_sql}
            GROUP BY fc.member_id
            HAVING COUNT(DISTINCT fc.pharmacy_id) >= :min_pharm
                OR COUNT(DISTINCT fc.prescriber_id) >= :min_presc
        ) sub
    """
    total = int(query_df(count_sql, params).iloc[0]["cnt"])

    shoppers = [
        DoctorShopper(
            member_id=int(r["member_id"]),
            member_name=str(r["member_name"]),  # PHI
            member_state=str(r["member_state"]) if pd.notna(r.get("member_state")) else None,
            pharmacy_count=int(r["pharmacy_count"]),
            prescriber_count=int(r["prescriber_count"]),
            controlled_fill_count=int(r["controlled_fill_count"]),
            total_exposure=round(float(r["total_exposure"]), 2),
            risk_bucket=str(r["risk_bucket"]),
            first_fill_date=r["first_fill_date"],
            last_fill_date=r["last_fill_date"],
        )
        for _, r in df.iterrows()
    ]

    return PaginatedResponse(total=total, offset=offset, limit=limit, data=shoppers)


# --- Pharmacy Hubs ---
@app.get("/pharmacy-hubs", response_model=PaginatedResponse)
def get_pharmacy_hubs(
    min_prescribers: int = Query(5, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse:
    sql = """
        SELECT
            ph.pharmacy_id, ph.pharmacy_name, ph.npi AS pharmacy_npi,
            ph.state AS pharmacy_state,
            COUNT(DISTINCT fc.prescriber_id) AS distinct_prescriber_count,
            COUNT(DISTINCT fc.member_id) AS distinct_member_count,
            COUNT(fc.claim_id) AS total_claims,
            SUM(fc.paid_amount) AS total_exposure,
            CASE
                WHEN COUNT(DISTINCT fc.prescriber_id) >= 20 THEN 'HIGH'
                WHEN COUNT(DISTINCT fc.prescriber_id) >= 10 THEN 'MEDIUM'
                ELSE 'LOW'
            END AS risk_bucket
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_pharmacy ph ON fc.pharmacy_id = ph.pharmacy_id
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
        GROUP BY ph.pharmacy_id, ph.pharmacy_name, ph.npi, ph.state
        HAVING COUNT(DISTINCT fc.prescriber_id) >= :min_prescribers
        ORDER BY distinct_prescriber_count DESC
        LIMIT :limit OFFSET :offset
    """
    params = {"min_prescribers": min_prescribers, "limit": limit, "offset": offset}
    df = query_df(sql, params)

    count_sql = """
        SELECT COUNT(*) AS cnt FROM (
            SELECT fc.pharmacy_id
            FROM network_graph.fact_pharmacy_claim fc
            JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
            WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
            GROUP BY fc.pharmacy_id
            HAVING COUNT(DISTINCT fc.prescriber_id) >= :min_prescribers
        ) sub
    """
    total = int(query_df(count_sql, {"min_prescribers": min_prescribers}).iloc[0]["cnt"])

    hubs = [
        PharmacyHub(
            pharmacy_id=int(r["pharmacy_id"]),
            pharmacy_name=str(r["pharmacy_name"]),
            pharmacy_npi=str(r["pharmacy_npi"]),
            pharmacy_state=str(r["pharmacy_state"]) if pd.notna(r.get("pharmacy_state")) else None,
            distinct_prescriber_count=int(r["distinct_prescriber_count"]),
            distinct_member_count=int(r["distinct_member_count"]),
            total_claims=int(r["total_claims"]),
            total_exposure=round(float(r["total_exposure"]), 2),
            risk_bucket=str(r["risk_bucket"]),
        )
        for _, r in df.iterrows()
    ]

    return PaginatedResponse(total=total, offset=offset, limit=limit, data=hubs)


# --- Geo Outliers ---
@app.get("/geo-outliers", response_model=PaginatedResponse)
def get_geo_outliers(
    min_miles: float = Query(50.0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse:
    sql = """
        SELECT
            sf.claim_id, sf.member_id, m.member_name, m.state AS member_state,
            m.zip AS member_zip, m.latitude AS member_lat, m.longitude AS member_lon,
            sf.pharmacy_id, ph.pharmacy_name, ph.state AS pharmacy_state,
            ph.zip AS pharmacy_zip, ph.latitude AS pharmacy_lat, ph.longitude AS pharmacy_lon,
            d.drug_name, d.drug_class,
            sf.fill_date, sf.paid_amount, sf.distance_miles, sf.risk_bucket
        FROM network_graph.fact_suspicious_fill sf
        JOIN network_graph.dim_member m ON sf.member_id = m.member_id
        JOIN network_graph.dim_pharmacy ph ON sf.pharmacy_id = ph.pharmacy_id
        JOIN network_graph.dim_drug d ON sf.drug_id = d.drug_id
        WHERE sf.rule_name = 'geo_anomaly'
            AND sf.distance_miles >= :min_miles
        ORDER BY sf.distance_miles DESC
        LIMIT :limit OFFSET :offset
    """
    params = {"min_miles": min_miles, "limit": limit, "offset": offset}
    df = query_df(sql, params)

    count_sql = """
        SELECT COUNT(*) AS cnt
        FROM network_graph.fact_suspicious_fill
        WHERE rule_name = 'geo_anomaly' AND distance_miles >= :min_miles
    """
    total = int(query_df(count_sql, {"min_miles": min_miles}).iloc[0]["cnt"])

    outliers = [
        GeoOutlier(
            claim_id=int(r["claim_id"]),
            member_id=int(r["member_id"]),
            member_name=str(r["member_name"]),  # PHI
            member_state=str(r["member_state"]) if pd.notna(r.get("member_state")) else None,
            member_zip=str(r["member_zip"]) if pd.notna(r.get("member_zip")) else None,
            pharmacy_id=int(r["pharmacy_id"]),
            pharmacy_name=str(r["pharmacy_name"]),
            pharmacy_state=str(r["pharmacy_state"]) if pd.notna(r.get("pharmacy_state")) else None,
            pharmacy_zip=str(r["pharmacy_zip"]) if pd.notna(r.get("pharmacy_zip")) else None,
            drug_name=str(r["drug_name"]) if pd.notna(r.get("drug_name")) else None,
            drug_class=str(r["drug_class"]) if pd.notna(r.get("drug_class")) else None,
            fill_date=r["fill_date"],
            paid_amount=round(float(r["paid_amount"]), 2),
            distance_miles=round(float(r["distance_miles"]), 2),
            risk_bucket=str(r["risk_bucket"]),
            member_lat=float(r["member_lat"]) if pd.notna(r.get("member_lat")) else None,
            member_lon=float(r["member_lon"]) if pd.notna(r.get("member_lon")) else None,
            pharmacy_lat=float(r["pharmacy_lat"]) if pd.notna(r.get("pharmacy_lat")) else None,
            pharmacy_lon=float(r["pharmacy_lon"]) if pd.notna(r.get("pharmacy_lon")) else None,
        )
        for _, r in df.iterrows()
    ]

    return PaginatedResponse(total=total, offset=offset, limit=limit, data=outliers)


# --- Config Rules ---
@app.get("/config/rules", response_model=list[ConfigRule])
def get_config_rules() -> list[ConfigRule]:
    df = query_df("SELECT * FROM network_graph.config_detection_rules ORDER BY rule_name, parameter_name")
    return [
        ConfigRule(
            rule_id=int(r["rule_id"]),
            rule_name=str(r["rule_name"]),
            parameter_name=str(r["parameter_name"]),
            parameter_value=str(r["parameter_value"]),
            description=str(r["description"]) if pd.notna(r.get("description")) else None,
            updated_at=r["updated_at"],
        )
        for _, r in df.iterrows()
    ]


@app.put("/config/rules", response_model=list[ConfigRule])
def update_config_rules(payload: ConfigRuleUpdate) -> list[ConfigRule]:
    for rule in payload.rules:
        execute(
            """
            INSERT INTO network_graph.config_detection_rules
                (rule_name, parameter_name, parameter_value, description, updated_at)
            VALUES (:rule_name, :param_name, :param_value, :description, CURRENT_TIMESTAMP)
            ON CONFLICT (rule_name, parameter_name)
            DO UPDATE SET
                parameter_value = :param_value,
                description = :description,
                updated_at = CURRENT_TIMESTAMP
            """,
            {
                "rule_name": rule.rule_name,
                "param_name": rule.parameter_name,
                "param_value": rule.parameter_value,
                "description": rule.description or "",
            },
        )
    return get_config_rules()
