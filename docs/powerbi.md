# Power BI Integration — Network Graph

## Overview

Network Graph exposes four flat, denormalized reporting views designed for Power BI DirectQuery or Import mode. All views live in the `network_graph` schema and contain no nested types, arrays, or JSON columns.

## Connection Setup

1. **Data Source**: PostgreSQL
2. **Server**: `localhost:5432` (or production host)
3. **Database**: `network_graph`
4. **Schema**: `network_graph`
5. **Authentication**: Database credentials (configure in Power BI Gateway for scheduled refresh)

## Reporting Views

### RPT_NETWORK_BUCKETS

Prescriber-pharmacy pairs linked by shared members filling controlled substances.

| Column | Type | Description |
|--------|------|-------------|
| prescriber_id | INT | Prescriber dimension key |
| prescriber_name | VARCHAR | Prescriber display name |
| prescriber_npi | VARCHAR | National Provider Identifier |
| specialty | VARCHAR | Prescriber medical specialty |
| pharmacy_id | INT | Pharmacy dimension key |
| pharmacy_name | VARCHAR | Pharmacy display name |
| pharmacy_npi | VARCHAR | Pharmacy NPI |
| shared_member_count | INT | Distinct members shared between this pair |
| risk_bucket | VARCHAR | HIGH / MEDIUM / LOW |
| total_exposure | NUMERIC | Sum of paid amounts for this pair |
| prescriber_state | VARCHAR | Prescriber state |
| pharmacy_state | VARCHAR | Pharmacy state |

### RPT_DOCTOR_SHOPPERS

Members visiting multiple pharmacies and/or prescribers for controlled substances.

| Column | Type | Description |
|--------|------|-------------|
| member_id | INT | Member dimension key |
| member_name | VARCHAR | **PHI** — Member name |
| member_state | VARCHAR | Member state |
| member_zip | VARCHAR | Member zip code |
| pharmacy_count | INT | Distinct pharmacies used |
| prescriber_count | INT | Distinct prescribers visited |
| controlled_fill_count | INT | Total controlled substance fills |
| total_exposure | NUMERIC | Total paid amount |
| risk_bucket | VARCHAR | HIGH / MEDIUM / LOW |
| first_fill_date | DATE | Earliest fill in period |
| last_fill_date | DATE | Latest fill in period |

### RPT_PHARMACY_HUBS

Pharmacies receiving controlled-substance prescriptions from many distinct prescribers.

| Column | Type | Description |
|--------|------|-------------|
| pharmacy_id | INT | Pharmacy dimension key |
| pharmacy_name | VARCHAR | Pharmacy display name |
| pharmacy_npi | VARCHAR | Pharmacy NPI |
| pharmacy_type | VARCHAR | Retail, Chain, Independent, etc. |
| pharmacy_state | VARCHAR | State |
| pharmacy_zip | VARCHAR | Zip code |
| distinct_prescriber_count | INT | Unique prescribers sending scripts |
| distinct_member_count | INT | Unique members filling |
| total_claims | INT | Total controlled fills |
| total_exposure | NUMERIC | Total paid amount |
| risk_bucket | VARCHAR | HIGH / MEDIUM / LOW |

### RPT_GEO_OUTLIERS

Flagged fills where member-to-pharmacy distance is anomalous.

| Column | Type | Description |
|--------|------|-------------|
| suspicious_fill_id | INT | Fact table key |
| claim_id | INT | Pharmacy claim key |
| member_id | INT | Member dimension key |
| member_name | VARCHAR | **PHI** — Member name |
| member_state | VARCHAR | Member state |
| member_zip | VARCHAR | Member zip |
| pharmacy_id | INT | Pharmacy dimension key |
| pharmacy_name | VARCHAR | Pharmacy name |
| pharmacy_state | VARCHAR | Pharmacy state |
| pharmacy_zip | VARCHAR | Pharmacy zip |
| drug_id | INT | Drug dimension key |
| drug_name | VARCHAR | Drug display name |
| drug_class | VARCHAR | Drug classification |
| fill_date | DATE | Fill date |
| paid_amount | NUMERIC | Paid amount |
| distance_miles | FLOAT | Haversine distance in miles |
| risk_bucket | VARCHAR | HIGH / MEDIUM / LOW |
| detection_details | TEXT | Human-readable detection note |

## Sample DAX Measures

```dax
// Total $ Exposure across all flagged networks
Total Exposure = SUM(RPT_NETWORK_BUCKETS[total_exposure])

// Count of unique members involved in doctor shopping
Doctor Shopper Count = COUNTROWS(RPT_DOCTOR_SHOPPERS)

// Average distance for geo outliers
Avg Outlier Distance = AVERAGE(RPT_GEO_OUTLIERS[distance_miles])

// Bucket distribution for networks
HIGH Network Count =
    CALCULATE(
        COUNTROWS(RPT_NETWORK_BUCKETS),
        RPT_NETWORK_BUCKETS[risk_bucket] = "HIGH"
    )

MEDIUM Network Count =
    CALCULATE(
        COUNTROWS(RPT_NETWORK_BUCKETS),
        RPT_NETWORK_BUCKETS[risk_bucket] = "MEDIUM"
    )

LOW Network Count =
    CALCULATE(
        COUNTROWS(RPT_NETWORK_BUCKETS),
        RPT_NETWORK_BUCKETS[risk_bucket] = "LOW"
    )

// Total members flagged across all detection rules
Total Flagged Members =
    CALCULATE(
        DISTINCTCOUNT(RPT_DOCTOR_SHOPPERS[member_id])
    ) +
    CALCULATE(
        DISTINCTCOUNT(RPT_GEO_OUTLIERS[member_id])
    )

// Pharmacy hub exposure as % of total
Hub Exposure Pct =
    DIVIDE(
        SUM(RPT_PHARMACY_HUBS[total_exposure]),
        CALCULATE(SUM(RPT_PHARMACY_HUBS[total_exposure]), ALL(RPT_PHARMACY_HUBS)),
        0
    )

// Top prescriber by shared member count
Top Prescriber Shared Members =
    MAXX(RPT_NETWORK_BUCKETS, RPT_NETWORK_BUCKETS[shared_member_count])
```

## Recommended Visuals

1. **Executive Summary Page**: KPI cards (Total Exposure, Flagged Members, Network Count), donut chart by risk_bucket, bar chart of top prescribers
2. **Network Detail Page**: Matrix visual with prescriber rows, pharmacy columns, shared_member_count values; conditional formatting by risk_bucket
3. **Doctor Shopping Page**: Table with member details, slicer by state, bar chart of pharmacy_count distribution
4. **Geo Outliers Page**: Map visual (ArcGIS or built-in) with member/pharmacy lat/lon, bubble size = distance_miles
5. **Pharmacy Hubs Page**: Bar chart of top hubs by prescriber count, table with drill-through to member details

## Notes

- All views are **flat** — no nested types, no arrays, no JSON. Safe for DirectQuery.
- PHI columns (`member_name`, `member_id`) are marked. Apply Row-Level Security (RLS) as needed.
- For Import mode: schedule refresh to match detection run cadence.
- Views reference `CONFIG_DETECTION_RULES` for bucket thresholds, so changing thresholds takes effect on next view query.
