-- Stored procedure: Network Bucket Detection (R2)

CREATE OR REPLACE FUNCTION network_graph.sp_detect_network_buckets(
    p_high_threshold INTEGER DEFAULT 60,
    p_medium_threshold INTEGER DEFAULT 20
)
RETURNS TABLE (
    prescriber_id INTEGER,
    pharmacy_id INTEGER,
    shared_member_count BIGINT,
    risk_bucket VARCHAR,
    total_exposure NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fc.prescriber_id,
        fc.pharmacy_id,
        COUNT(DISTINCT fc.member_id) AS shared_member_count,
        CASE
            WHEN COUNT(DISTINCT fc.member_id) > p_high_threshold THEN 'HIGH'
            WHEN COUNT(DISTINCT fc.member_id) > p_medium_threshold THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR AS risk_bucket,
        SUM(fc.paid_amount) AS total_exposure
    FROM network_graph.fact_pharmacy_claim fc
    JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
    WHERE d.is_controlled = TRUE OR d.is_commonly_abused = TRUE
    GROUP BY fc.prescriber_id, fc.pharmacy_id
    ORDER BY shared_member_count DESC;
END;
$$ LANGUAGE plpgsql;
