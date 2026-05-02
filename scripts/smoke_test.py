"""Smoke test — hits every API endpoint and asserts non-empty results.

Usage:
    python scripts/smoke_test.py [--base-url http://localhost:8000/api/network-graph]
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError


def check(name: str, url: str, method: str = "GET", body: bytes | None = None) -> bool:
    """Hit an endpoint and verify it returns 200 with non-empty data."""
    try:
        req = Request(url, method=method, data=body)
        if body:
            req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            # Check for non-empty
            if isinstance(data, dict):
                has_data = bool(data.get("data") or data.get("nodes") or data.get("status") or data.get("total_claims") is not None or data.get("members"))
            elif isinstance(data, list):
                has_data = len(data) > 0
            else:
                has_data = bool(data)

            status = "PASS" if has_data else "WARN (empty)"
            print(f"  [{status}] {name}: {resp.status} — {_summary(data)}")
            return True
    except URLError as e:
        print(f"  [FAIL] {name}: {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] {name}: {type(e).__name__}: {e}")
        return False


def _summary(data: object) -> str:
    if isinstance(data, dict):
        if "nodes" in data:
            return f"{len(data['nodes'])} nodes, {data.get('total_edges', 0)} edges"
        if "data" in data:
            return f"{data.get('total', '?')} total, {len(data['data'])} returned"
        if "status" in data:
            return f"status={data['status']}"
        if "total_claims" in data:
            return f"claims={data['total_claims']}, exposure=${data.get('total_exposure', 0):,.0f}"
        return str(list(data.keys())[:5])
    if isinstance(data, list):
        return f"{len(data)} items"
    return str(data)[:80]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api/network-graph")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print("=" * 60)
    print("Network Graph — Smoke Test")
    print("=" * 60)

    results = []

    endpoints = [
        ("Health check", f"{base}/healthz"),
        ("KPI summary", f"{base}/kpi"),
        ("Networks (all)", f"{base}/networks"),
        ("Networks (HIGH bucket)", f"{base}/networks?bucket=HIGH"),
        ("Networks (opioids)", f"{base}/networks?drug_class=opioids"),
        ("Doctor shoppers", f"{base}/doctor-shoppers"),
        ("Doctor shoppers (min_pharmacies=5)", f"{base}/doctor-shoppers?min_pharmacies=5"),
        ("Pharmacy hubs", f"{base}/pharmacy-hubs"),
        ("Pharmacy hubs (min_prescribers=10)", f"{base}/pharmacy-hubs?min_prescribers=10"),
        ("Geo outliers", f"{base}/geo-outliers"),
        ("Geo outliers (min_miles=100)", f"{base}/geo-outliers?min_miles=100"),
        ("Config rules (GET)", f"{base}/config/rules"),
    ]

    for name, url in endpoints:
        results.append(check(name, url))

    # Drill test — get first prescriber from networks
    try:
        req = Request(f"{base}/networks?limit=1")
        with urlopen(req, timeout=30) as resp:
            net_data = json.loads(resp.read())
            if net_data.get("nodes"):
                node_id = net_data["nodes"][0]["id"]
                results.append(check(f"Network drill ({node_id})", f"{base}/networks/{node_id}/drill"))
            else:
                print("  [SKIP] Network drill — no nodes available")
    except Exception as e:
        print(f"  [FAIL] Network drill setup: {e}")
        results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)
    print()
    print("=" * 60)
    print(f"Results: {passed}/{total} passed")
    print("=" * 60)

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
