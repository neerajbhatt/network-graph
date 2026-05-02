-- Stored procedure: Geo-Distance Anomaly Detection (R6)
-- Uses Haversine formula in SQL

CREATE OR REPLACE FUNCTION network_graph.sp_detect_geo_anomalies(
    p_absolute_miles DOUBLE PRECISION DEFAULT 50.0
)
RETURNS TABLE (
    claim_id INTEGER,
    member_id INTEGER,
    prescriber_id INTEGER,
    pharmacy_id INTEGER,
    drug_id INTEGER,
    fill_date DATE,
    paid_amount NUMERIC,
    distance_miles DOUBLE PRECISION,
    risk_bucket VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH distances AS (
        SELECT
            fc.claim_id, fc.member_id, fc.prescriber_id, fc.pharmacy_id,
            fc.drug_id, fc.fill_date, fc.paid_amount,
            3958.8 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(ph.latitude - m.latitude) / 2), 2) +
                COS(RADIANS(m.latitude)) * COS(RADIANS(ph.latitude)) *
                POWER(SIN(RADIANS(ph.longitude - m.longitude) / 2), 2)
            )) AS dist_miles
        FROM network_graph.fact_pharmacy_claim fc
        JOIN network_graph.dim_member m ON fc.member_id = m.member_id
        JOIN network_graph.dim_pharmacy ph ON fc.pharmacy_id = ph.pharmacy_id
        JOIN network_graph.dim_drug d ON fc.drug_id = d.drug_id
        WHERE (d.is_controlled = TRUE OR d.is_commonly_abused = TRUE)
            AND m.latitude IS NOT NULL AND ph.latitude IS NOT NULL
    )
    SELECT
        d.claim_id, d.member_id, d.prescriber_id, d.pharmacy_id,
        d.drug_id, d.fill_date, d.paid_amount,
        ROUND(d.dist_miles::NUMERIC, 2)::DOUBLE PRECISION AS distance_miles,
        CASE
            WHEN d.dist_miles > p_absolute_miles * 3 THEN 'HIGH'
            WHEN d.dist_miles > p_absolute_miles THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR AS risk_bucket
    FROM distances d
    WHERE d.dist_miles > p_absolute_miles
    ORDER BY d.dist_miles DESC;
END;
$$ LANGUAGE plpgsql;
