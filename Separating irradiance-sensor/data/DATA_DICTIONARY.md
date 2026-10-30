# Data dictionary

Only the variables read by the analysis are included. Site and stations are anonymised at the host institution's request;
solar geometry uses the grid point 20.0° N, 100.0° E (Asia/Bangkok, UTC+7).

## daily_zone_data.csv
One row per zone and day, 3 March 2023 – 7 September 2026 (3 zones; 12 duplicated zone-days already removed;
2024-05-31 and 2024-08-07 missing). Empty cell = missing.

| Column | Unit | Description |
|---|---|---|
| date | YYYY-MM-DD (local) | Calendar day |
| zone | – | Zone 1 (2,256.3 kWp), Zone 2 (207.0 kWp), Zone 3 (49.9 kWp) |
| equivalent_hours | kWh kWp⁻¹ (h) | Final yield Y_f reported by the monitoring platform |
| pr_percent | % | Reported performance ratio; stored as min(PR, 90.00) by the platform |
| ambient_temp_mean_c | °C | Daily mean ambient temperature of the zone station |
| flag_pr_truncated | bool | True when the reported PR is ≥ 89.95 % (clipped value; used as a censored observation) |
| include_trend_event | bool | Day used in the analysis: after commissioning (≥ 2023-04-26), not an outage (output > 0, PR present, Y_f ≥ 0.5 h), irradiance and PR plausibility checks passed |

The own-sensor insolation of a zone is recovered as H = Y_f / (PR/100) on days with an unclipped PR.

## om_log.csv
Operation and maintenance log as supplied by the hospital engineering unit (Buddhist-calendar dates converted to Gregorian).

| Column | Description |
|---|---|
| code | C1–C7 panel cleaning; M1 meter calibration; T1 transformer maintenance |
| date_gregorian | Logged date |
| intervention | Logged action |
