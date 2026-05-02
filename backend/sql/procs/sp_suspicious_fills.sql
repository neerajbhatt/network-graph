-- Stored procedure: Suspicious Fills Detection (R1)
-- Flags pharmacy fills for controlled drugs without a supporting visit

CREATE OR REPLACE FUNCTION network_graph.sp_detect_suspicious_fills(
    p_lookback_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    claim_id INTEGER,
    member_id INTEGER,
    prescriber_id INTEGER,
    pharmacy_id INTEGER,
    drug_id INTEGER,
    fill_date DATE,
    paid_amount NUMERIC,
    days_since_last_visit INTEGER,
    risk_bucket VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH controlled_fills AS (
        SELECT
            fc.claim_id, fc.member_id, fc.prescriber_id, fc.pharmacy_id,
            fc.drug_id, fc.fill_date, fc.paid_amount
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
    ),
    all_visits AS (
        SELECT member_id, service_date AS visit_date FROM network_graph.fact_medical_claim
        UNION ALL
        SELECT member_id, service_date AS visit_date FROM network_graph.fact_dental_claim
    ),
    fills_with_visits AS (
        SELECT
            cf.*,
            MAX(av.visit_date) AS last_visit_date,
            cf.fill_date - MAX(av.visit_date) AS days_gap
        FROM controlled_fills cf
        LEFT JOIN all_visits av
            ON cf.member_id = av.member_id
            AND av.visit_date <= cf.fill_date
            AND av.visit_date >= cf.fill_date - p_lookback_days
        GROUP BY cf.claim_id, cf.member_id, cf.prescriber_id, cf.pharmacy_id,
                 cf.drug_id, cf.fill_date, cf.paid_amount
    )
    SELECT
        fwv.claim_id, fwv.member_id, fwv.prescriber_id, fwv.pharmacy_id,
        fwv.drug_id, fwv.fill_date, fwv.paid_amount,
        COALESCE(fwv.days_gap, -1)::INTEGER AS days_since_last_visit,
        CASE
            WHEN fwv.last_visit_date IS NULL THEN 'HIGH'
            WHEN fwv.days_gap > p_lookback_days * 2 THEN 'HIGH'
            WHEN fwv.days_gap > p_lookback_days THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR AS risk_bucket
    FROM fills_with_visits fwv
    WHERE fwv.last_visit_date IS NULL;
END;
$$ LANGUAGE plpgsql;
