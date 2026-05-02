-- Seed CONFIG_DETECTION_RULES with default thresholds

INSERT INTO network_graph.config_detection_rules (rule_name, parameter_name, parameter_value, description) VALUES
-- R1 — Suspicious fills
('suspicious_fills', 'lookback_days_default', '30', 'Default lookback window in days for medical/dental visit check'),
('suspicious_fills', 'lookback_days_opioids', '30', 'Lookback for opioid class'),
('suspicious_fills', 'lookback_days_benzodiazepines', '30', 'Lookback for benzodiazepine class'),
('suspicious_fills', 'lookback_days_stimulants', '30', 'Lookback for stimulant class'),
('suspicious_fills', 'lookback_days_gabapentinoids', '45', 'Lookback for gabapentinoid class (longer due to chronic pain patterns)'),
('suspicious_fills', 'lookback_days_muscle_relaxants', '30', 'Lookback for muscle relaxant class'),

-- R2 — Network buckets
('network_buckets', 'high_threshold', '60', 'Shared member count above this = HIGH bucket'),
('network_buckets', 'medium_threshold', '20', 'Shared member count above this = MEDIUM bucket'),

-- R4.2 — Doctor shopping
('doctor_shopping', 'min_pharmacies', '3', 'Minimum distinct pharmacies to flag'),
('doctor_shopping', 'min_prescribers', '3', 'Minimum distinct prescribers to flag'),

-- R4.3 — Pharmacy hubs
('pharmacy_hubs', 'min_prescribers', '5', 'Minimum distinct prescribers to flag a pharmacy as hub'),

-- R6 — Geo anomaly
('geo_anomaly', 'absolute_miles', '50', 'Absolute distance threshold in miles'),
('geo_anomaly', 'percentile', '95', '95th percentile of member history triggers flag')
ON CONFLICT (rule_name, parameter_name) DO UPDATE SET parameter_value = EXCLUDED.parameter_value, updated_at = CURRENT_TIMESTAMP;
