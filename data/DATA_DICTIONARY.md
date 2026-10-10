# Data dictionary — czmr_daily_zone_curated.csv.gz

3,849 zone-days (3 zones × 1,283 observed days, 3 Mar 2023 – 7 Sep 2026; 12 duplicate zone-days removed). Missing calendar days: 2024-05-31, 2024-08-07. Missing values are empty cells. Time zone: Asia/Bangkok.

| Column | Type | Unit | Description |
|---|---|---|---|
| source_file | text | – | Platform export file the row came from (export date in file name, YYYYMMDDhhmmss) |
| date | date (YYYY-MM-DD) | local day, Asia/Bangkok (UTC+7) | Calendar day of the record |
| zone | text | – | Monitoring zone (anonymised): Zone 1/2/3 |
| n_intervals | integer | count | Number of 30-min intervals aggregated (48 = complete day) |
| daily_production_kwh | float | kWh | PV AC energy of the zone |
| daily_load_kwh | float | kWh | Site load attributed to the zone meter (= production + purchased − exported) |
| daily_purchased_kwh | float | kWh | Grid purchase recorded at the zone meter |
| daily_exported_kwh | float | kWh | Export to grid |
| equivalent_hours | float | kWh kWp⁻¹ (h) | Final yield Y_f reported by the platform |
| pr_percent | float | % | Reported performance ratio; upper-truncated at 90.00 by the reporting layer; empty = missing |
| ambient_temp_mean_c | float | °C | Daily mean ambient temperature |
| statuses | text (Thai) | – | ปกติ = normal; สัญญาณเตือน = alarm; ฟอลต์ = fault |
| alarm_flag | boolean | – | True if status is alarm |
| ref_insolation_H3_kwh_m2 | float | kWh m⁻² | Zone 3 implied horizontal insolation (Y_f,3 / PR_3), common reference |
| avoided_price_thb_kwh | float | THB kWh⁻¹ | Daily avoided-energy price: PEA TOU 4.2.2 + Ft + 7 % VAT (a3c_tariff.py) |
| prc_common_ref | float | – | Common-reference, thermally corrected PR (Eq. 6); empty when excluded |
| flag_outage_invalid | boolean | – | R2: production ≤ 0, PR missing or Y_f < 0.5 h |
| flag_pr_truncated | boolean | – | R4: reported PR ≥ 89.95 % (reporting-layer truncation) |
| flag_commissioning | boolean | – | R3: date before 2023-04-26 |
| flag_low_insolation | boolean | – | R5: H3 < 1 kWh m⁻² or missing |
| flag_prc_out_of_range | boolean | – | R5: PRc outside 0.3–1.2 |
| include_trend_event | boolean | – | Row used in trend and event analyses |
| include_own_sensor_H | boolean | – | Row usable for own-sensor insolation H_i |
| clear_day_H3_ge3 | boolean | – | Sensitivity S1: clear day |
| event_window | text | – | Event window membership, e.g. C6_pre / C6_gap / C6_post (primary windows) |

Removed duplicates are listed in removed_duplicates.csv. Exclusion rules: EXCLUSION_RULES.md / exclusion_rules.json. O&M log with Buddhist-calendar entries and cleaning-procedure class: om_log.csv.
