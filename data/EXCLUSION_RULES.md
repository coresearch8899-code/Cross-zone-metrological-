# Exclusion rules and quality-control flags (applied in this order)

| ID | Rule | Flag column |
|---|---|---|
| R1 | remove duplicated (date, zone) rows, keep last export | flag_duplicate (removed_duplicates.csv) |
| R2 | outage/invalid: production <= 0 kWh or PR missing or Yf < 0.5 h | flag_outage_invalid |
| R3 | commissioning: date < 2023-04-26 excluded from trend/event analyses | flag_commissioning |
| R4 | reported PR >= 89.95 % treated as truncated; own-sensor insolation H_i only on untruncated days | flag_pr_truncated / include_own_sensor_H |
| R5 | common-reference metrics: exclude H3 < 1 kWh/m2 and PRc outside 0.3-1.2 | flag_low_insolation / flag_prc_out_of_range |
| R6 | no imputation; statistics on available days | - |
| S1 | sensitivity: clear days only, H3 >= 3 kWh/m2 | clear_day_H3_ge3 |

Event windows: pre = d-14..d-1, gap = d0..d+3, post = d+4..d+17 (primary); sensitivity windows 7/14/21/28 d and gaps 1/3/5 d.
