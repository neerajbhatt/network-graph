-- Stored procedure: Pharmacy Hub Detection (R4.3)

CREATE OR REPLACE FUNCTION network_graph.sp_detect_pharmacy_hubs(
    p_min_prescribers INTEGER DEFAULT 5
)
RETURNS TABLE (
    pharmacy_id INTEGER,
    distinct_prescriber_count BIGINT,
    distinct_member_count BIGINT,
    total_claims BIGINT,
    total_exposure NUMERIC,
    risk_bucket VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fc.pharmacy_id,
        COUNT(DISTINCT fc.prescriber_id) AS distinct_prescriber_count,
        COUNT(DISTINCT fc.member_id) AS distinct_member_count,
        COUNT(fc.claim_id) AS total_claims,
        SUM(fc.paid_amount) AS total_exposure,
        CASE
            WHEN COUNT(DISTINCT fc.prescriber_id) >= 20 THEN 'HIGH'
            WHEN COUNT(DISTINCT fc.prescriber_id) >= 10 THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR AS risk_bucket
    FROM network_graph.fact_pharmacy_claim fc
    JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
    WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
    GROUP BY fc.pharmacy_id
    HAVING COUNT(DISTINCT fc.prescriber_id) >= p_min_prescribers
    ORDER BY distinct_prescriber_count DESC;
END;
$$ LANGUAGE plpgsql;
