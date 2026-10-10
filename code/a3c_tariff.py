"""Step 3c (R6): time-varying avoided-energy price for self-consumed PV under the PEA Large General Service TOU tariff
(rate 4.2; energy charges unchanged from the May 2023 to the September 2026 schedule), retail Ft by billing period
(PEA Ft statistics), 7 % VAT. Demand-charge savings are not counted (conservative).
On-Peak 09:00-22:00 Mon-Fri; Off-Peak 22:00-09:00 Mon-Fri and all day Sat, Sun and regular public holidays.
The share of daily PV energy produced before 09:00 is taken from the clear-sky horizontal profile at the regional grid point."""
import pandas as pd, numpy as np, pvlib, json
LAT, LON, ALT = 20.0, 100.0, 400        # regional grid point (exact site withheld)
RATES = {'4.2.1 (>=69 kV)': (4.1025, 2.5849), '4.2.2 (22-33 kV)': (4.1839, 2.6037), '4.2.3 (<22 kV)': (4.3297, 2.6369)}
CENTRAL = '4.2.2 (22-33 kV)'
FT = [('2023-01-01', '2023-04-30', 1.5492), ('2023-05-01', '2023-08-31', 0.9119), ('2023-09-01', '2023-12-31', 0.2048),
      ('2024-01-01', '2024-12-31', 0.3972), ('2025-01-01', '2025-04-30', 0.3672), ('2025-05-01', '2025-08-31', 0.1972),
      ('2025-09-01', '2025-12-31', 0.1572), ('2026-01-01', '2026-04-30', 0.0972), ('2026-05-01', '2026-12-31', 0.1623)]
VAT = 1.07
HOL = ['2023-03-06', '2023-04-06', '2023-04-13', '2023-04-14', '2023-04-15', '2023-05-01', '2023-05-04', '2023-06-03', '2023-07-28', '2023-08-01', '2023-08-02', '2023-08-12', '2023-10-13', '2023-10-23', '2023-12-05', '2023-12-10', '2023-12-31',
       '2024-01-01', '2024-02-24', '2024-04-06', '2024-04-13', '2024-04-14', '2024-04-15', '2024-05-01', '2024-05-04', '2024-05-22', '2024-06-03', '2024-07-20', '2024-07-21', '2024-07-28', '2024-08-12', '2024-10-13', '2024-10-23', '2024-12-05', '2024-12-10', '2024-12-31',
       '2025-01-01', '2025-02-12', '2025-04-06', '2025-04-13', '2025-04-14', '2025-04-15', '2025-05-01', '2025-05-04', '2025-05-11', '2025-06-03', '2025-07-10', '2025-07-11', '2025-07-28', '2025-08-12', '2025-10-13', '2025-10-23', '2025-12-05', '2025-12-10', '2025-12-31',
       '2026-01-01', '2026-03-03', '2026-04-06', '2026-04-13', '2026-04-14', '2026-04-15', '2026-05-01', '2026-05-04', '2026-05-31', '2026-06-03', '2026-07-28', '2026-07-29', '2026-07-30', '2026-08-12']
days = pd.date_range('2023-03-01', '2026-09-30', freq='D')
t = pd.date_range(days[0], days[-1] + pd.Timedelta(days=1), freq='10min', tz='Asia/Bangkok')
cs = pvlib.location.Location(LAT, LON, 'Asia/Bangkok', ALT).get_clearsky(t, model='ineichen').ghi
morning = cs[cs.index.hour < 9].resample('D').sum() / cs.resample('D').sum()
morning.index = morning.index.tz_localize(None); morning = morning.reindex(days)
ft = pd.Series(np.nan, index=days)
for a, b, v in FT: ft[a:b] = v
offday = (days.dayofweek >= 5) | days.isin(pd.to_datetime(HOL))
def price(cls, morning_scale=1.0):
    on, off = RATES[cls]; fm = (morning * morning_scale).clip(0, 1)
    energy = np.where(offday, off, (1 - fm) * on + fm * off)
    return pd.Series((energy + ft.values) * VAT, index=days)
P = pd.DataFrame({cls: price(cls) for cls in RATES})
P['central'] = P[CENTRAL]; P['low'] = price('4.2.1 (>=69 kV)', 1.3); P['high'] = price('4.2.3 (<22 kV)', 0.7)
P.to_pickle('tariff_daily.pkl')
d = pd.read_pickle('d_clean.pkl'); E1 = d[d.z == 1].set_index('date').daily_production_kwh
w = E1.reindex(P.index).fillna(0)
out = {'class_central': CENTRAL, 'morning_share_mean': round(float(morning.mean()), 3), 'offpeak_day_share': round(float(offday[(days >= '2023-03-03') & (days <= '2026-09-07')].mean()), 3),
       'energy_weighted_price_THB_kWh': {c: round(float((P[c] * w).sum() / w.sum()), 3) for c in P.columns},
       'by_year_central': {int(y): round(float((P['central'] * w)[str(y)].sum() / w[str(y)].sum()), 3) for y in [2023, 2024, 2025, 2026]},
       'dry_DecMar_central': round(float((P['central'] * w)[P.index.month.isin([12, 1, 2, 3])].sum() / w[P.index.month.isin([12, 1, 2, 3])].sum()), 3),
       'wet_MayOct_central': round(float((P['central'] * w)[P.index.month.isin(range(5, 11))].sum() / w[P.index.month.isin(range(5, 11))].sum()), 3)}
json.dump(out, open('res_tariff.json', 'w'), indent=1); print(json.dumps(out, indent=1))
