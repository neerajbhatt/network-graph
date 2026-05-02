-- Stored procedure: Doctor Shopping Detection (R4.2)

CREATE OR REPLACE FUNCTION network_graph.sp_detect_doctor_shoppers(
    p_min_pharmacies INTEGER DEFAULT 3,
    p_min_prescribers INTEGER DEFAULT 3
)
RETURNS TABLE (
    member_id INTEGER,
    pharmacy_count BIGINT,
    prescriber_count BIGINT,
    controlled_fill_count BIGINT,
    total_exposure NUMERIC,
    risk_bucket VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fc.member_id,
        COUNT(DISTINCT fc.pharmacy_id) AS pharmacy_count,
        COUNT(DISTINCT fc.prescriber_id) AS prescriber_count,
        COUNT(fc.claim_id) AS controlled_fill_count,
        SUM(fc.paid_amount) AS total_exposure,
        CASE
            WHEN COUNT(DISTINCT fc.pharmacy_id) >= 5 OR COUNT(DISTINCT fc.prescriber_id) >= 5 THEN 'HIGH'
            WHEN COUNT(DISTINCT fc.pharmacy_id) >= 3 OR COUNT(DISTINCT fc.prescriber_id) >= 3 THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR AS risk_bucket
    FROM network_graph.fact_pharmacy_claim fc
    JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
    WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
    GROUP BY fc.member_id
    HAVING COUNT(DISTINCT fc.pharmacy_id) >= p_min_pharmacies
        OR COUNT(DISTINCT fc.prescriber_id) >= p_min_prescribers
    ORDER BY total_exposure DESC;
END;
$$ LANGUAGE plpgsql;
