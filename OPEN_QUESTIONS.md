# Open Questions — Network Graph

## Q1 — Real Data Source Connectivity
**Question**: What are the actual Snowflake/warehouse credentials and connection details for production data?
**Default assumed**: Postgres local with synthetic data. `DATA_MODE=REAL` expects tables pre-populated via ETL.
**Impact if wrong**: Connection layer swap needed.

## Q2 — PHI Encryption at Rest
**Question**: Does the production deployment require column-level encryption for PHI fields, or is database-level encryption sufficient?
**Default assumed**: Synthetic mode has no real PHI. Columns are annotated `# PHI` for future implementation.
**Impact if wrong**: Need to add pgcrypto or application-level encryption.

## Q3 — NDC Code Completeness
**Question**: Should `REF_CONTROLLED_DRUGS` be seeded from a specific formulary or the full FDA NDC directory?
**Default assumed**: 50+ representative NDCs across DEA Schedule II–V and commonly abused drug classes.
**Impact if wrong**: May need bulk NDC import pipeline.

## Q4 — Network Identity Resolution
**Question**: How are prescribers and pharmacies deduplicated? By NPI alone, or is there a master data source?
**Default assumed**: NPI is the unique key for prescribers; NCPDP/NPI for pharmacies.
**Impact if wrong**: Need entity resolution layer.

## Q5 — Role-Based Access Control
**Question**: What roles and permissions are needed for the web UI? Should SIU analysts see different data than leadership?
**Default assumed**: Single-role access for v1. RBAC deferred.
**Impact if wrong**: Need auth middleware and role-based query filters.

## Q6 — Alert/Case Management Integration
**Question**: Should flagged cases push to an existing case management system (e.g., NICE Actimize, SAS)?
**Default assumed**: No integration for v1. Reporting views are the hand-off point.
**Impact if wrong**: Need webhook/API integration layer.

## Q7 — Lookback Per Drug Class Values
**Question**: What are the clinically appropriate lookback windows per drug class?
**Default assumed**: 30 days for all classes. Config table allows per-class overrides.
**Impact if wrong**: May need clinical pharmacist review of defaults.

## Q8 — Dollar Exposure Calculation
**Question**: Should $ exposure use paid amount, billed amount, or allowed amount?
**Default assumed**: Using `paid_amount` from pharmacy claims.
**Impact if wrong**: Column rename or additional amount fields needed.

## Q9 — Geographic Threshold Calibration
**Question**: Is the 50-mile default appropriate across urban/rural markets?
**Default assumed**: 50 miles absolute threshold + 95th percentile of member history.
**Impact if wrong**: May need market-adjusted thresholds.

## Q10 — Power BI Gateway Configuration
**Question**: Will Power BI connect via DirectQuery to Postgres or import mode?
**Default assumed**: DirectQuery to the RPT_* views. Documentation provided.
**Impact if wrong**: May need to optimize views for import mode refresh.
