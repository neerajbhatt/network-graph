# Architecture — Network Graph

## System Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  React SPA  │────▶│  FastAPI     │────▶│  PostgreSQL  │
│  (Vite)     │     │  /api/       │     │  network_graph│
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    │ network_  │
                    │ graph_core│
                    │ (detectors)│
                    └───────────┘
```

## Entity Relationship Diagram

```mermaid
erDiagram
    DIM_MEMBER {
        int member_id PK
        varchar member_name "PHI"
        date dob "PHI"
        varchar gender
        varchar address "PHI"
        varchar city
        varchar state
        varchar zip
        float latitude
        float longitude
        date enrollment_start
        date enrollment_end
    }

    DIM_PRESCRIBER {
        int prescriber_id PK
        varchar npi
        varchar prescriber_name
        varchar specialty
        varchar address
        varchar city
        varchar state
        varchar zip
        float latitude
        float longitude
    }

    DIM_PHARMACY {
        int pharmacy_id PK
        varchar npi
        varchar pharmacy_name
        varchar pharmacy_type
        varchar address
        varchar city
        varchar state
        varchar zip
        float latitude
        float longitude
    }

    DIM_DRUG {
        int drug_id PK
        varchar ndc
        varchar drug_name
        varchar drug_class
        varchar dea_schedule
        boolean is_controlled
        boolean is_commonly_abused
    }

    FACT_PHARMACY_CLAIM {
        int claim_id PK
        int member_id FK
        int prescriber_id FK
        int pharmacy_id FK
        int drug_id FK
        date fill_date
        int days_supply
        int quantity
        decimal paid_amount
        varchar claim_status
    }

    FACT_MEDICAL_CLAIM {
        int claim_id PK
        int member_id FK
        int prescriber_id FK
        date service_date
        varchar procedure_code
        varchar diagnosis_code
        varchar place_of_service
        decimal paid_amount
        varchar claim_status
    }

    FACT_DENTAL_CLAIM {
        int claim_id PK
        int member_id FK
        int prescriber_id FK
        date service_date
        varchar procedure_code
        varchar diagnosis_code
        decimal paid_amount
        varchar claim_status
    }

    FACT_SUSPICIOUS_FILL {
        int suspicious_fill_id PK
        int claim_id FK
        int member_id FK
        int prescriber_id FK
        int pharmacy_id FK
        int drug_id FK
        date fill_date
        decimal paid_amount
        varchar rule_name
        varchar risk_bucket
        int days_since_last_visit
        float distance_miles
        varchar detection_details
        timestamp detected_at
        int audit_run_id FK
    }

    REF_CONTROLLED_DRUGS {
        int ref_drug_id PK
        varchar ndc
        varchar drug_name
        varchar drug_class
        varchar dea_schedule
        boolean is_controlled
        boolean is_commonly_abused
    }

    CONFIG_DETECTION_RULES {
        int rule_id PK
        varchar rule_name
        varchar parameter_name
        varchar parameter_value
        varchar description
        timestamp updated_at
    }

    AUDIT_DETECTION_RUNS {
        int run_id PK
        varchar rule_name
        varchar rule_version
        timestamp run_timestamp
        int input_count
        int flagged_count
        varchar status
        text details
    }

    RPT_NETWORK_BUCKETS {
        int prescriber_id
        varchar prescriber_name
        int pharmacy_id
        varchar pharmacy_name
        int shared_member_count
        varchar risk_bucket
        decimal total_exposure
    }

    RPT_DOCTOR_SHOPPERS {
        int member_id
        varchar member_name
        int pharmacy_count
        int prescriber_count
        int controlled_fill_count
        decimal total_exposure
        varchar risk_bucket
    }

    RPT_PHARMACY_HUBS {
        int pharmacy_id
        varchar pharmacy_name
        int distinct_prescriber_count
        int distinct_member_count
        decimal total_exposure
        varchar risk_bucket
    }

    RPT_GEO_OUTLIERS {
        int claim_id
        int member_id
        int pharmacy_id
        float distance_miles
        decimal paid_amount
        varchar risk_bucket
    }

    DIM_MEMBER ||--o{ FACT_PHARMACY_CLAIM : "has fills"
    DIM_MEMBER ||--o{ FACT_MEDICAL_CLAIM : "has visits"
    DIM_MEMBER ||--o{ FACT_DENTAL_CLAIM : "has visits"
    DIM_PRESCRIBER ||--o{ FACT_PHARMACY_CLAIM : "prescribes"
    DIM_PRESCRIBER ||--o{ FACT_MEDICAL_CLAIM : "treats"
    DIM_PRESCRIBER ||--o{ FACT_DENTAL_CLAIM : "treats"
    DIM_PHARMACY ||--o{ FACT_PHARMACY_CLAIM : "dispenses"
    DIM_DRUG ||--o{ FACT_PHARMACY_CLAIM : "filled as"
    FACT_PHARMACY_CLAIM ||--o{ FACT_SUSPICIOUS_FILL : "flagged by"
    AUDIT_DETECTION_RUNS ||--o{ FACT_SUSPICIOUS_FILL : "produced by"
```

## Detection Pipeline

```
Claims Data ──▶ Suspicious Fill Detector (R1)
             ──▶ Network Bucket Detector (R2)
             ──▶ Doctor Shopping Detector (R4.2)
             ──▶ Pharmacy Hub Detector (R4.3)
             ──▶ Geo Anomaly Detector (R6)
                      │
                      ▼
              FACT_SUSPICIOUS_FILL
              RPT_* Summary Views
                      │
                      ▼
              API ──▶ Frontend / Power BI
```

## Key Design Patterns

1. **Detector Interface**: Each detector is a pure function: `detect(df, config) -> DataFrame`
2. **Config-Driven**: All thresholds in `CONFIG_DETECTION_RULES`, loaded at detection time
3. **Audit Trail**: Every detection run logs to `AUDIT_DETECTION_RUNS`
4. **Star Schema**: Fact tables reference dimension tables via integer FKs for Power BI compatibility
