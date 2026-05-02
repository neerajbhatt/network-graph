-- Dimension tables for Network Graph

CREATE TABLE IF NOT EXISTS network_graph.dim_member (
    member_id       SERIAL PRIMARY KEY,
    member_name     VARCHAR(200),       -- PHI
    dob             DATE,               -- PHI
    gender          VARCHAR(10),
    address         VARCHAR(300),       -- PHI
    city            VARCHAR(100),
    state           VARCHAR(2),
    zip             VARCHAR(10),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    enrollment_start DATE,
    enrollment_end   DATE
);

CREATE INDEX idx_dim_member_state ON network_graph.dim_member(state);
CREATE INDEX idx_dim_member_zip ON network_graph.dim_member(zip);

CREATE TABLE IF NOT EXISTS network_graph.dim_prescriber (
    prescriber_id   SERIAL PRIMARY KEY,
    npi             VARCHAR(10) UNIQUE NOT NULL,
    prescriber_name VARCHAR(200),
    specialty       VARCHAR(100),
    address         VARCHAR(300),
    city            VARCHAR(100),
    state           VARCHAR(2),
    zip             VARCHAR(10),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION
);

CREATE INDEX idx_dim_prescriber_npi ON network_graph.dim_prescriber(npi);
CREATE INDEX idx_dim_prescriber_specialty ON network_graph.dim_prescriber(specialty);
CREATE INDEX idx_dim_prescriber_state ON network_graph.dim_prescriber(state);

CREATE TABLE IF NOT EXISTS network_graph.dim_pharmacy (
    pharmacy_id     SERIAL PRIMARY KEY,
    npi             VARCHAR(10) UNIQUE NOT NULL,
    pharmacy_name   VARCHAR(200),
    pharmacy_type   VARCHAR(50),
    address         VARCHAR(300),
    city            VARCHAR(100),
    state           VARCHAR(2),
    zip             VARCHAR(10),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION
);

CREATE INDEX idx_dim_pharmacy_npi ON network_graph.dim_pharmacy(npi);
CREATE INDEX idx_dim_pharmacy_state ON network_graph.dim_pharmacy(state);

CREATE TABLE IF NOT EXISTS network_graph.dim_drug (
    drug_id             SERIAL PRIMARY KEY,
    ndc                 VARCHAR(20) UNIQUE NOT NULL,
    drug_name           VARCHAR(300),
    drug_class          VARCHAR(100),
    dea_schedule        VARCHAR(10),
    is_controlled       BOOLEAN DEFAULT FALSE,
    is_commonly_abused  BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_dim_drug_ndc ON network_graph.dim_drug(ndc);
CREATE INDEX idx_dim_drug_class ON network_graph.dim_drug(drug_class);
