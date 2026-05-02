-- Reporting views — flat, Power BI-friendly, no nested types

-- RPT_NETWORK_BUCKETS: Prescriber-Pharmacy network pairs with shared member counts
CREATE OR REPLACE VIEW network_graph.rpt_network_buckets AS
SELECT
    pr.prescriber_id,
    pr.prescriber_name,
    pr.npi AS prescriber_npi,
    pr.specialty,
    ph.pharmacy_id,
    ph.pharmacy_name,
    ph.npi AS pharmacy_npi,
    COUNT(DISTINCT fc.member_id) AS shared_member_count,
    CASE
        WHEN COUNT(DISTINCT fc.member_id) > (
            SELECT CAST(parameter_value AS INTEGER) FROM network_graph.config_detection_rules
            WHERE rule_name = 'network_buckets' AND parameter_name = 'high_threshold'
        ) THEN 'HIGH'
        WHEN COUNT(DISTINCT fc.member_id) > (
            SELECT CAST(parameter_value AS INTEGER) FROM network_graph.config_detection_rules
            WHERE rule_name = 'network_buckets' AND parameter_name = 'medium_threshold'
        ) THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_bucket,
    SUM(fc.paid_amount) AS total_exposure,
    pr.state AS prescriber_state,
    ph.state AS pharmacy_state
FROM network_graph.fact_pharmacy_claim fc
JOIN network_graph.dim_prescriber pr ON fc.prescriber_id = pr.prescriber_id
JOIN network_graph.dim_pharmacy ph ON fc.pharmacy_id = ph.pharmacy_id
JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
GROUP BY pr.prescriber_id, pr.prescriber_name, pr.npi, pr.specialty,
         ph.pharmacy_id, ph.pharmacy_name, ph.npi, pr.state, ph.state;

-- RPT_DOCTOR_SHOPPERS: Members visiting multiple pharmacies/prescribers
CREATE OR REPLACE VIEW network_graph.rpt_doctor_shoppers AS
SELECT
    m.member_id,
    m.member_name,                          -- PHI
    m.state AS member_state,
    m.zip AS member_zip,
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
WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
GROUP BY m.member_id, m.member_name, m.state, m.zip;

-- RPT_PHARMACY_HUBS: Pharmacies receiving from many distinct prescribers
CREATE OR REPLACE VIEW network_graph.rpt_pharmacy_hubs AS
SELECT
    ph.pharmacy_id,
    ph.pharmacy_name,
    ph.npi AS pharmacy_npi,
    ph.pharmacy_type,
    ph.state AS pharmacy_state,
    ph.zip AS pharmacy_zip,
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
GROUP BY ph.pharmacy_id, ph.pharmacy_name, ph.npi, ph.pharmacy_type, ph.state, ph.zip;

-- RPT_GEO_OUTLIERS: Claims where member-pharmacy distance is anomalous
CREATE OR REPLACE VIEW network_graph.rpt_geo_outliers AS
SELECT
    sf.suspicious_fill_id,
    sf.claim_id,
    sf.member_id,
    m.member_name,                          -- PHI
    m.state AS member_state,
    m.zip AS member_zip,
    sf.pharmacy_id,
    ph.pharmacy_name,
    ph.state AS pharmacy_state,
    ph.zip AS pharmacy_zip,
    sf.drug_id,
    d.drug_name,
    d.drug_class,
    sf.fill_date,
    sf.paid_amount,
    sf.distance_miles,
    sf.risk_bucket,
    sf.detection_details
FROM network_graph.fact_suspicious_fill sf
JOIN network_graph.dim_member m ON sf.member_id = m.member_id
JOIN network_graph.dim_pharmacy ph ON sf.pharmacy_id = ph.pharmacy_id
JOIN network_graph.dim_drug d ON sf.drug_id = d.drug_id
WHERE sf.rule_name = 'geo_anomaly';
