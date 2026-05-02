-- Detection and audit tables

CREATE TABLE IF NOT EXISTS network_graph.ref_controlled_drugs (
    ref_drug_id         SERIAL PRIMARY KEY,
    ndc                 VARCHAR(20),
    drug_name           VARCHAR(300),
    drug_class          VARCHAR(100),
    dea_schedule        VARCHAR(10),
    is_controlled       BOOLEAN DEFAULT TRUE,
    is_commonly_abused  BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_rcd_ndc ON network_graph.ref_controlled_drugs(ndc);
CREATE INDEX idx_rcd_class ON network_graph.ref_controlled_drugs(drug_class);

CREATE TABLE IF NOT EXISTS network_graph.config_detection_rules (
    rule_id         SERIAL PRIMARY KEY,
    rule_name       VARCHAR(100) NOT NULL,
    parameter_name  VARCHAR(100) NOT NULL,
    parameter_value VARCHAR(200) NOT NULL,
    description     TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rule_name, parameter_name)
);

CREATE TABLE IF NOT EXISTS network_graph.audit_detection_runs (
    run_id          SERIAL PRIMARY KEY,
    rule_name       VARCHAR(100) NOT NULL,
    rule_version    VARCHAR(20) DEFAULT '1.0',
    run_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_count     INTEGER DEFAULT 0,
    flagged_count   INTEGER DEFAULT 0,
    status          VARCHAR(20) DEFAULT 'COMPLETED',
    details         TEXT
);

CREATE TABLE IF NOT EXISTS network_graph.fact_suspicious_fill (
    suspicious_fill_id  SERIAL PRIMARY KEY,
    claim_id            INTEGER REFERENCES network_graph.fact_pharmacy_claim(claim_id),
    member_id           INTEGER REFERENCES network_graph.dim_member(member_id),
    prescriber_id       INTEGER REFERENCES network_graph.dim_prescriber(prescriber_id),
    pharmacy_id         INTEGER REFERENCES network_graph.dim_pharmacy(pharmacy_id),
    drug_id             INTEGER REFERENCES network_graph.dim_drug(drug_id),
    fill_date           DATE,
    paid_amount         NUMERIC(12, 2),
    rule_name           VARCHAR(100),
    risk_bucket         VARCHAR(20),
    days_since_last_visit INTEGER,
    distance_miles      DOUBLE PRECISION,
    detection_details   TEXT,
    detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    audit_run_id        INTEGER REFERENCES network_graph.audit_detection_runs(run_id)
);

CREATE INDEX idx_fsf_member ON network_graph.fact_suspicious_fill(member_id);
CREATE INDEX idx_fsf_prescriber ON network_graph.fact_suspicious_fill(prescriber_id);
CREATE INDEX idx_fsf_pharmacy ON network_graph.fact_suspicious_fill(pharmacy_id);
CREATE INDEX idx_fsf_rule ON network_graph.fact_suspicious_fill(rule_name);
CREATE INDEX idx_fsf_bucket ON network_graph.fact_suspicious_fill(risk_bucket);
