-- Fact tables for Network Graph

CREATE TABLE IF NOT EXISTS network_graph.fact_pharmacy_claim (
    claim_id        SERIAL PRIMARY KEY,
    member_id       INTEGER NOT NULL REFERENCES network_graph.dim_member(member_id),
    prescriber_id   INTEGER NOT NULL REFERENCES network_graph.dim_prescriber(prescriber_id),
    pharmacy_id     INTEGER NOT NULL REFERENCES network_graph.dim_pharmacy(pharmacy_id),
    drug_id         INTEGER NOT NULL REFERENCES network_graph.dim_drug(drug_id),
    fill_date       DATE NOT NULL,
    days_supply     INTEGER,
    quantity         INTEGER,
    paid_amount     NUMERIC(12, 2),
    claim_status    VARCHAR(20) DEFAULT 'PAID'
);

CREATE INDEX idx_fpc_member ON network_graph.fact_pharmacy_claim(member_id);
CREATE INDEX idx_fpc_prescriber ON network_graph.fact_pharmacy_claim(prescriber_id);
CREATE INDEX idx_fpc_pharmacy ON network_graph.fact_pharmacy_claim(pharmacy_id);
CREATE INDEX idx_fpc_drug ON network_graph.fact_pharmacy_claim(drug_id);
CREATE INDEX idx_fpc_fill_date ON network_graph.fact_pharmacy_claim(fill_date);

CREATE TABLE IF NOT EXISTS network_graph.fact_medical_claim (
    claim_id        SERIAL PRIMARY KEY,
    member_id       INTEGER NOT NULL REFERENCES network_graph.dim_member(member_id),
    prescriber_id   INTEGER NOT NULL REFERENCES network_graph.dim_prescriber(prescriber_id),
    service_date    DATE NOT NULL,
    procedure_code  VARCHAR(20),
    diagnosis_code  VARCHAR(20),
    place_of_service VARCHAR(50),
    paid_amount     NUMERIC(12, 2),
    claim_status    VARCHAR(20) DEFAULT 'PAID'
);

CREATE INDEX idx_fmc_member ON network_graph.fact_medical_claim(member_id);
CREATE INDEX idx_fmc_prescriber ON network_graph.fact_medical_claim(prescriber_id);
CREATE INDEX idx_fmc_service_date ON network_graph.fact_medical_claim(service_date);

CREATE TABLE IF NOT EXISTS network_graph.fact_dental_claim (
    claim_id        SERIAL PRIMARY KEY,
    member_id       INTEGER NOT NULL REFERENCES network_graph.dim_member(member_id),
    prescriber_id   INTEGER NOT NULL REFERENCES network_graph.dim_prescriber(prescriber_id),
    service_date    DATE NOT NULL,
    procedure_code  VARCHAR(20),
    diagnosis_code  VARCHAR(20),
    paid_amount     NUMERIC(12, 2),
    claim_status    VARCHAR(20) DEFAULT 'PAID'
);

CREATE INDEX idx_fdc_member ON network_graph.fact_dental_claim(member_id);
CREATE INDEX idx_fdc_prescriber ON network_graph.fact_dental_claim(prescriber_id);
CREATE INDEX idx_fdc_service_date ON network_graph.fact_dental_claim(service_date);
